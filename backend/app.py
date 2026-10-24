import logging

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from backend.guardrails.routes import router as guardrails_router
from backend.database.db import get_connection
from backend.evaluation.evaluator import calculate_evaluation
from backend.evaluation.laya import evaluate_with_laya
from backend.evaluation.schemas import EvaluationRequest, EvaluationResponse
from backend.ingestion.routes import router as ingestion_router
from backend.rag.routes import router as chat_router


app = FastAPI(
    title="RAG Evalution API",
    description="Backend API for the DocuLens RAG document system.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the document ingestion API.
app.include_router(ingestion_router)
app.include_router(guardrails_router)
app.include_router(chat_router)


@app.get("/", tags=["General"])
def root():
    return {
        "application": "RAG Evalution",
        "chatbot": "DocuLens",
        "status": "running",
        "documentation": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": "RAG Evalution",
    }


@app.get("/health/database", tags=["Health"])
def database_health_check():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {"status": "healthy", "database": "connected"}

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable or incorrectly configured.",
        ) from error


@app.post(
    "/evaluate",
    response_model=EvaluationResponse,
    tags=["Evaluation"],
)
def evaluate_rag(request: EvaluationRequest):
    """Evaluate a RAG answer and save its evaluation results."""

    # Step 1: Run Laya and calculate the evaluation.
    try:
        laya_result = evaluate_with_laya(
            question=request.question,
            retrieved_context=request.retrieved_context,
            answer=request.generated_answer,
        )

        evaluation = calculate_evaluation(laya_result)

    except Exception as error:
        logger.exception("Laya evaluation failed.")

        raise HTTPException(
            status_code=502,
            detail="RAG evaluation failed. Check the server terminal.",
        ) from error

    # Step 2: Save the evaluation to PostgreSQL.
    try:
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
                        request.question,
                        evaluation["retrieval_relevance"],
                        None,
                        evaluation["faithfulness"],
                        evaluation["answer_relevance"],
                        None,
                        evaluation["safety_compliance"],
                        evaluation["overall_score"],
                        evaluation["decision"],
                        evaluation["reason"],
                        request.document_id,
                        request.conversation_id,
                    ),
                )

                result = cursor.fetchone()

                if not result:
                    raise RuntimeError(
                        "The evaluation record was not returned."
                    )

                evaluation_id = result[0]

    except Exception as error:
        logger.exception("Evaluation database save failed.")

        raise HTTPException(
            status_code=500,
            detail="Could not save the evaluation to the database.",
        ) from error

    # Step 3: Return the four scores and final decision.
    return {
        "evaluation_id": evaluation_id,
        **evaluation,
    }
