from typing import Any


MIN_RELEVANCE_SIMILARITY = 0.30


def check_relevance(
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check whether retrieved chunks meet the minimum relevance score."""

    if not retrieved_chunks:
        return {
            "relevant": False,
            "reason": "No document chunks were retrieved.",
            "top_similarity": None,
        }

    similarities = []

    for chunk in retrieved_chunks:
        similarity = chunk.get("similarity")

        if (
            isinstance(similarity, (int, float))
            and not isinstance(similarity, bool)
        ):
            similarities.append(float(similarity))

    if not similarities:
        return {
            "relevant": False,
            "reason": "Retrieved chunks have no valid similarity scores.",
            "top_similarity": None,
        }

    top_similarity = max(similarities)

    if top_similarity < MIN_RELEVANCE_SIMILARITY:
        return {
            "relevant": False,
            "reason": (
                "Retrieved chunks did not meet the minimum "
                "similarity requirement."
            ),
            "top_similarity": round(top_similarity, 4),
        }

    return {
        "relevant": True,
        "reason": "Retrieved chunks passed the similarity check.",
        "top_similarity": round(top_similarity, 4),
    }