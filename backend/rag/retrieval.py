import math

from pgvector.psycopg import register_vector

from backend.database.db import get_connection
from backend.rag.embeddings import EMBEDDING_DIMENSION


DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.30
CANDIDATE_MULTIPLIER = 20


def retrieve_relevant_chunks(
    question_embedding: list[float],
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[dict]:

    # Validate the question embedding.
    if not isinstance(question_embedding, (list, tuple)):
        raise TypeError("Question embedding must be a list of numbers.")

    if len(question_embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Question embedding must contain "
            f"{EMBEDDING_DIMENSION} values."
        )

    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        for value in question_embedding
    ):
        raise ValueError("Question embedding contains invalid values.")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    if (
        not isinstance(similarity_threshold, (int, float))
        or isinstance(similarity_threshold, bool)
        or not math.isfinite(similarity_threshold)
        or not 0 <= similarity_threshold <= 1
    ):
        raise ValueError(
            "Similarity threshold must be between 0 and 1."
        )

    candidate_limit = top_k * CANDIDATE_MULTIPLIER

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    dc.id,
                    dc.document_id,
                    d.file_name,
                    dc.chunk_index,
                    dc.chunk_text,
                    dc.metadata,
                    1 - (dc.embedding <=> %s::vector) AS similarity
                FROM document_chunks AS dc
                JOIN documents AS d
                    ON d.id = dc.document_id
                WHERE d.status = 'completed'
                  AND dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s;
                """,
                (
                    list(question_embedding),
                    list(question_embedding),
                    candidate_limit,
                ),
            )

            rows = cursor.fetchall()

    results = []

    # Filter invalid or weak matches.
    for row in rows:
        similarity = float(row[6])

        if not math.isfinite(similarity):
            continue

        if similarity < similarity_threshold:
            continue

        chunk_text = row[4]

        if not isinstance(chunk_text, str) or not chunk_text.strip():
            continue

        results.append(
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "file_name": row[2],
                "chunk_index": row[3],
                "chunk_text": chunk_text,
                "metadata": row[5],
                "similarity": similarity,
            }
        )

    # Sort strongest matches first.
    results.sort(
        key=lambda chunk: chunk["similarity"],
        reverse=True,
    )

    # Remove duplicate text while preserving the strongest match.
    unique_results = []
    seen_texts = set()

    for chunk in results:
        normalized_text = " ".join(
            chunk["chunk_text"].split()
        ).casefold()

        if normalized_text in seen_texts:
            continue

        seen_texts.add(normalized_text)
        unique_results.append(chunk)

        if len(unique_results) >= top_k:
            break

    return unique_results