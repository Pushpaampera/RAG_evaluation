import re


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150

# Prefer paragraph breaks, sentence endings, or whitespace.
BOUNDARY_PATTERN = re.compile(
    r"\n\s*\n+|(?<=[.!?])\s+|\s+"
)

WORD_PATTERN = re.compile(r"\S+")


def chunk_document(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """
    Create character-based, sentence-aware chunks with overlap.

    Preserves chunk_index, chunk_text, and word_count fields.
    """

    if not isinstance(text, str):
        raise ValueError("Document text must be a string.")

    if (
        not isinstance(chunk_size, int)
        or isinstance(chunk_size, bool)
        or chunk_size <= 0
    ):
        raise ValueError("Chunk size must be a positive integer.")

    if (
        not isinstance(overlap, int)
        or isinstance(overlap, bool)
        or overlap < 0
        or overlap >= chunk_size
    ):
        raise ValueError(
            "Overlap must be zero or greater and smaller than chunk size."
        )

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        target_end = min(start + chunk_size, text_length)
        end = target_end

        if target_end < text_length:
            # Prefer a natural boundary in the latter part
            # of the current chunk.
            minimum_boundary = start + int(chunk_size * 0.70)

            boundaries = [
                match.end()
                for match in BOUNDARY_PATTERN.finditer(
                    text,
                    minimum_boundary,
                    target_end,
                )
            ]

            if boundaries:
                end = boundaries[-1]
            else:
                # Fall back to a whitespace boundary.
                whitespace_position = text.rfind(
                    " ",
                    minimum_boundary,
                    target_end,
                )

                if whitespace_position > start:
                    end = whitespace_position

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "chunk_text": chunk_text,
                    "word_count": len(
                        WORD_PATTERN.findall(chunk_text)
                    ),
                }
            )

        if end >= text_length:
            break

        # Move forward while retaining overlap.
        next_start = max(start + 1, end - overlap)

        # Avoid starting in the middle of a word.
        while (
            next_start < end
            and not text[next_start - 1].isspace()
            and not text[next_start].isspace()
        ):
            next_start += 1

        start = next_start

    return chunks