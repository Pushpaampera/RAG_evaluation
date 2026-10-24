from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    if not text.strip():
        raise ValueError("Cannot generate an embedding for empty text.")

    model = get_embedding_model()

    embedding = model.encode(
        text.strip(),
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"received {len(embedding)}."
        )

    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not isinstance(texts, list):
        raise TypeError("Input must be a list of strings.")

    if not texts:
        return []

    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("Every text must be a non-empty string.")

    model = get_embedding_model()

    embeddings = model.encode(
        [text.strip() for text in texts],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    if embeddings.shape != (len(texts), EMBEDDING_DIMENSION):
        raise ValueError("The embedding model returned an unexpected shape.")

    return embeddings.tolist()