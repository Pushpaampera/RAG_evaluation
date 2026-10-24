import re
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.evaluation.evaluator import calculate_evaluation
from backend.evaluation.laya import evaluate_with_laya
from backend.guardrails.service import get_active_rules
from backend.database.db import get_connection
from backend.llm.gemini import generate_answer
from backend.rag.embeddings import embed_text
from backend.rag.memory import add_message, get_history
from backend.rag.prompts import NOT_FOUND_MESSAGE
from backend.rag.relevance import check_relevance
from backend.rag.retrieval import retrieve_relevant_chunks


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

MAX_QUESTION_LENGTH = 10_000
MAX_TOP_K = 5


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=MAX_QUESTION_LENGTH,
    )
    conversation_id: str | None = Field(
        default=None,
        max_length=100,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=MAX_TOP_K,
    )


def save_evaluation(
    question: str,
    context: str,
    answer: str,
    document_id: int | None,
    conversation_id: str,
) -> dict | None:
    """Evaluate an answer and save its four evaluation scores."""

    try:
        # Run Laya evaluation.
        laya_result = evaluate_with_laya(
            question=question,
            retrieved_context=context,
            answer=answer,
        )
        

        # Convert probabilities into scores and a final decision.
        evaluation = calculate_evaluation(laya_result)

        logger.info(
            "Evaluation completed: score=%s, decision=%s",
            evaluation["overall_score"],
            evaluation["decision"],
        )

       

        # Save the four scores.
        # The existing database still has six criterion columns.
        # The two removed criteria are stored as NULL.
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO rag_evaluations (
                        question,
                        retrieval_relevance,
                        context_relevance,
                        faithfulness,
                        answer_relevance,
                        boundary_compliance,
                        safety_compliance,
                        overall_score,
                        decision,
                        reason,
                        document_id,
                        conversation_id
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id;
                    """,
                    (
                        question,
                        evaluation["retrieval_relevance"],
                        None,
                        evaluation["faithfulness"],
                        evaluation["answer_relevance"],
                        None,
                        evaluation["safety_compliance"],
                        evaluation["overall_score"],
                        evaluation["decision"],
                        evaluation["reason"],
                        document_id,
                        conversation_id,
                    ),
                )

                result = cursor.fetchone()

                if not result:
                    raise RuntimeError(
                        "The evaluation record was not returned."
                    )

                evaluation_id = result[0]

        return {
            "evaluation_id": evaluation_id,
            **evaluation,
        }

    except Exception:
        # Evaluation failures should not destroy a valid chat answer.
        logger.exception(
            "Chat answer evaluation or persistence failed."
        )
        return None


@router.post("/")
def chat(request: ChatRequest):
    """Answer questions using retrieved document context."""

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Please enter a question.",
        )

    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=422,
            detail="The question exceeds the permitted length.",
        )

    conversation_id = request.conversation_id or str(uuid4())

    
    greeting_answer = get_greeting_response(question)

    if greeting_answer is not None:
        add_message(conversation_id, "user", question)
        add_message(
            conversation_id,
            "assistant",
            greeting_answer,
        )

        return {
            "conversation_id": conversation_id,
            "answer": greeting_answer,
            "sources": [],
            "relevance": None,
            "guardrails": {
                "input": "ALLOW",
                "output": "NOT_CHECKED",
            },
            "evaluation": None,
        }

    
    # 2. Load guardrail rules.
    

    try:
        input_rules = get_active_rules("input")
        output_rules = get_active_rules("output")
        safety_rules = get_active_rules("safety")

    except Exception as error:
        logger.exception(
            "Could not load active guardrail rules."
        )

        raise HTTPException(
            status_code=503,
            detail="Guardrail configuration is unavailable.",
        ) from error

    # Basic input validation.
    if any(
        rule["enabled"] and rule["name"] == "Input Validation"
        for rule in input_rules
    ) and not question:
        raise HTTPException(
            status_code=422,
            detail="The question cannot be empty.",
        )

   

    history = get_history(conversation_id)

   
    # 4. Generate the question embedding and retrieve chunks.
   

    try:
        question_embedding = embed_text(question)

        chunks = retrieve_relevant_chunks(
            question_embedding=question_embedding,
            top_k=request.top_k,
        )

        relevance = check_relevance(chunks)

    except Exception as error:
        logger.exception("Question retrieval failed.")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve document information.",
        ) from error

    
    # 5. Prepare source information for the frontend.
    

    sources = [
        {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "file_name": chunk["file_name"],
            "chunk_index": chunk["chunk_index"],
            "similarity": round(
                float(chunk["similarity"]),
                4,
            ),
        }
        for chunk in chunks
    ]

    
    # 6. Handle questions with no relevant retrieved context.
   

    if not relevance["relevant"]:
        answer = NOT_FOUND_MESSAGE

        add_message(conversation_id, "user", question)
        add_message(
            conversation_id,
            "assistant",
            answer,
        )

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": [],
            "relevance": relevance,
            "guardrails": {
                "input": "ALLOW",
                "output": "NOT_CHECKED",
                "active_output_rules": len(output_rules),
                "active_safety_rules": len(safety_rules),
            },
            "evaluation": None,
        }

    
    # 7. Build the retrieved context.
    

    context = "\n\n".join(
        (
            f"Source: {chunk['file_name']}\n"
            f"{chunk['chunk_text']}"
        )
        for chunk in chunks
    )

    # 8. Generate the answer using Gemini.
    

    try:
        answer = generate_answer(
            question=question,
            retrieved_chunks=chunks,
            history=history,
        )

    except Exception as error:
        logger.exception("Answer generation failed.")

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not generate an answer. "
                "Check the backend logs."
            ),
        ) from error

    if not answer or not answer.strip():
        raise HTTPException(
            status_code=502,
            detail="The answer generator returned an empty response.",
        )

   
    # 9. Evaluate the answer and persist the four scores.
   
    evaluation = save_evaluation(
        question=question,
        context=context,
        answer=answer,
        document_id=chunks[0]["document_id"],
        conversation_id=conversation_id,
    )

   
    # 10. Save the conversation history.
   
    add_message(conversation_id, "user", question)
    add_message(
        conversation_id,
        "assistant",
        answer,
    )

   
    # 11. Return the answer, sources, and evaluation.
    
    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources,
        "relevance": relevance,
        "guardrails": {
            "input": "ALLOW",
            "output": "NOT_CHECKED",
            "active_output_rules": len(output_rules),
            "active_safety_rules": len(safety_rules),
        },
        "evaluation": evaluation,
    }



# GREETING HANDLER

GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|"
    r"good morning|good afternoon|good evening|"
    r"how are you|how are you doing|"
    r"thank you|thanks|"
    r"who are you|who are u|"
    r"what can you do|"
    r"what is your name|"
    r"what's your name|"
    r"help)"
    r"[!?.\s]*$",
    re.IGNORECASE,
)


def get_greeting_response(question: str) -> str | None:
    """Return a response to common greetings and assistant questions."""

    clean_question = " ".join(question.strip().split())

    if not GREETING_PATTERN.fullmatch(clean_question):
        return None

    normalized = clean_question.lower().strip(" !?.")

    if normalized in {"hi", "hello", "hey"}:
        return (
            "Hello! 👋 I'm DocuLens AI, your document-grounded "
            "assistant. Ask me questions about your uploaded "
            "documents, and I'll help you find answers, summarize "
            "information, and explore relevant sources."
        )

    if normalized == "good morning":
        return (
            "Good morning! ☀️ How can I help you explore "
            "your documents today?"
        )

    if normalized == "good afternoon":
        return (
            "Good afternoon! How can I help you with "
            "your documents today?"
        )

    if normalized == "good evening":
        return (
            "Good evening! How can I help you with "
            "your documents today?"
        )

    if normalized in {"how are you", "how are you doing"}:
        return (
            "I'm ready to help! Ask me about your uploaded "
            "documents, or tell me what information you're looking for."
        )

    if normalized in {"thank you", "thanks"}:
        return (
            "You're welcome! Feel free to ask another question."
        )

    if normalized in {"who are you", "who are u"}:
        return (
            "I'm DocuLens AI. I help you retrieve information "
            "from uploaded documents, explain key details, and "
            "inspect answer sources and evaluation results when available."
        )

    if normalized in {"what is your name", "what's your name"}:
        return (
            "I'm DocuLens AI, your document-grounded assistant."
        )

    return (
        "I can help you search, understand, and summarize "
        "information from your uploaded documents. "
        "What would you like to explore?"
    )