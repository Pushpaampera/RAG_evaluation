from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=10000,
    )

    retrieved_context: str = Field(
        min_length=1,
        max_length=50000,
    )

    generated_answer: str = Field(
        min_length=1,
        max_length=20000,
    )

    document_id: int | None = None 

    conversation_id: str | None = Field(
        default=None,
        max_length=100,
    )


class EvaluationResponse(BaseModel):
    evaluation_id: int
    retrieval_relevance: float
    faithfulness: float
    answer_relevance: float
    safety_compliance: float
    overall_score: float
    decision: str
    reason: str
