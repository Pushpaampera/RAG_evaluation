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






















# from backend.database.db import get_connection


# def initialize_schema() -> None:
#     """
#     Initialize the PostgreSQL schema required by RAG Evalution.

#     Creates the pgvector extension, application tables,
#     and indexes if they do not already exist.
#     """

#     with get_connection() as connection:
#         with connection.cursor() as cursor:

           

#             cursor.execute(
#                 """
#                 CREATE EXTENSION IF NOT EXISTS vector;
#                 """
#             )

            

#             cursor.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS documents (
#                     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

#                     file_name TEXT NOT NULL,
#                     file_type VARCHAR(10) NOT NULL,
#                     file_size BIGINT NOT NULL,

#                     status VARCHAR(20) NOT NULL DEFAULT 'uploaded',

#                     uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

#                     CONSTRAINT documents_file_type_check
#                         CHECK (file_type IN ('pdf', 'docx')),

#                     CONSTRAINT documents_file_size_check
#                         CHECK (file_size >= 0),

#                     CONSTRAINT documents_status_check
#                         CHECK (
#                             status IN (
#                                 'uploaded',
#                                 'processing',
#                                 'completed',
#                                 'failed',
#                                 'rejected'
#                             )
#                         )
#                 );
#                 """
#             )

           

#             cursor.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS document_chunks (
#                     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

#                     document_id BIGINT NOT NULL,

#                     chunk_index INTEGER NOT NULL,
#                     chunk_text TEXT NOT NULL,

#                     embedding VECTOR(384) NOT NULL,

#                     metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

#                     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

#                     CONSTRAINT document_chunks_document_fk
#                         FOREIGN KEY (document_id)
#                         REFERENCES documents(id)
#                         ON DELETE CASCADE,

#                     CONSTRAINT document_chunks_index_check
#                         CHECK (chunk_index >= 0),

#                     CONSTRAINT document_chunks_text_check
#                         CHECK (LENGTH(TRIM(chunk_text)) > 0),

#                     CONSTRAINT document_chunks_unique_index
#                         UNIQUE (document_id, chunk_index)
#                 );
#                 """
#             )

            

#             cursor.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS guardrail_rules (
#                     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

#                     name VARCHAR(150) NOT NULL,
#                     description TEXT NOT NULL,
#                     category VARCHAR(30) NOT NULL,

#                     rule_text TEXT NOT NULL,

#                     enabled BOOLEAN NOT NULL DEFAULT TRUE,

#                     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
#                     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

#                     CONSTRAINT guardrail_rules_category_check
#                         CHECK (
#                             category IN (
#                                 'input',
#                                 'retrieval',
#                                 'output',
#                                 'scope',
#                                 'safety',
#                                 'ingestion'
#                             )
#                         ),

#                     CONSTRAINT guardrail_rules_name_check
#                         CHECK (LENGTH(TRIM(name)) > 0),

#                     CONSTRAINT guardrail_rules_text_check
#                         CHECK (LENGTH(TRIM(rule_text)) > 0)
#                 );
#                 """
#             )

            

#             cursor.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS rag_evaluations (
#                     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

#                     question TEXT NOT NULL,

#                     retrieval_relevance NUMERIC(4, 2),
#                     context_relevance NUMERIC(4, 2),
#                     faithfulness NUMERIC(4, 2),
#                     answer_relevance NUMERIC(4, 2),

#                     boundary_compliance NUMERIC(4, 2),
#                     safety_compliance NUMERIC(4, 2),

#                     overall_score NUMERIC(4, 2),

#                     decision VARCHAR(20) NOT NULL,

#                     reason TEXT NOT NULL,

#                     document_id BIGINT,

#                     conversation_id VARCHAR(100),

#                     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

#                     CONSTRAINT rag_evaluations_document_fk
#                         FOREIGN KEY (document_id)
#                         REFERENCES documents(id)
#                         ON DELETE SET NULL,

#                     CONSTRAINT rag_evaluations_decision_check
#                         CHECK (
#                             decision IN (
#                                 'PASS',
#                                 'NEEDS_REVIEW',
#                                 'FAIL'
#                             )
#                         ),

#                     CONSTRAINT rag_evaluations_scores_check
#                         CHECK (
#                             (
#                                 retrieval_relevance IS NULL
#                                 OR retrieval_relevance BETWEEN 0 AND 10
#                             )
#                             AND (
#                                 context_relevance IS NULL
#                                 OR context_relevance BETWEEN 0 AND 10
#                             )
#                             AND (
#                                 faithfulness IS NULL
#                                 OR faithfulness BETWEEN 0 AND 10
#                             )
#                             AND (
#                                 answer_relevance IS NULL
#                                 OR answer_relevance BETWEEN 0 AND 10
#                             )
#                             AND (
#                                 boundary_compliance IS NULL
#                                 OR boundary_compliance BETWEEN 0 AND 10
#                             )
#                             AND (
#                                 safety_compliance IS NULL
#                                 OR safety_compliance BETWEEN 0 AND 10
#                             )
#                             AND (
#                                 overall_score IS NULL
#                                 OR overall_score BETWEEN 0 AND 10
#                             )
#                         )
#                 );
#                 """
#             )

           

#             cursor.execute(
#                 """
#                 CREATE INDEX IF NOT EXISTS idx_documents_status
#                 ON documents(status);
#                 """
#             )

#             cursor.execute(
#                 """
#                 CREATE INDEX IF NOT EXISTS idx_chunks_document_id
#                 ON document_chunks(document_id);
#                 """
#             )

#             cursor.execute(
#                 """
#                 CREATE INDEX IF NOT EXISTS idx_guardrail_rules_enabled
#                 ON guardrail_rules(enabled);
#                 """
#             )

#             cursor.execute(
#                 """
#                 CREATE INDEX IF NOT EXISTS idx_guardrail_rules_category
#                 ON guardrail_rules(category);
#                 """
#             )

#             cursor.execute(
#                 """
#                 CREATE INDEX IF NOT EXISTS idx_rag_evaluations_created_at
#                 ON rag_evaluations(created_at DESC);
#                 """
#             )

#     print("Database schema initialized successfully.")
#     print("pgvector extension enabled.")
#     print("Created or verified all four application tables.")
#     print("Database indexes created or verified.")


# if __name__ == "__main__":
#     initialize_schema()