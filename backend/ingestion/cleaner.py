import re


# TEXT CLEANING CONFIGURATION

MULTIPLE_SPACES = re.compile(r"[ \t]+")
MULTIPLE_BLANK_LINES = re.compile(r"\n{3,}")

HEADING_PATTERN = re.compile(r"^#{1,6}\s+")
LIST_PATTERN = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])\s+"
)
NUMBERED_PAGE_PATTERN = re.compile(
    r"^##\s+Page\s+\d+\s*$",
    re.IGNORECASE,
)


def is_structural_line(line: str) -> bool:
    """
    Identify lines whose structure should be preserved.
    """

    stripped = line.strip()

    if not stripped:
        return False

    if HEADING_PATTERN.match(stripped):
        return True

    if LIST_PATTERN.match(stripped):
        return True

    if NUMBERED_PAGE_PATTERN.match(stripped):
        return True

    # Preserve table rows.
    if "|" in stripped:
        return True

    return False


def clean_text(text: str) -> str:
    """
    Clean extracted document text while preserving meaning.

    Operations:
        1. Normalize line endings.
        2. Remove unnecessary whitespace.
        3. Preserve headings and list items.
        4. Join wrapped paragraph lines.
        5. Preserve paragraph boundaries.
        6. Remove excessive blank lines.

    Parameters:
        text: Raw text extracted from a document.

    Returns:
        Cleaned text as a string.
    """

    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    if not text.strip():
        return ""

   
    # 1. NORMALIZE LINE ENDINGS
    
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    
    # 2. NORMALIZE EACH LINE
    
    lines = []

    for line in text.split("\n"):
        line = MULTIPLE_SPACES.sub(" ", line).strip()
        lines.append(line)

    
    # 3. PRESERVE DOCUMENT STRUCTURE
  

    blocks = []
    paragraph_lines = []

    def flush_paragraph():
        """
        Combine wrapped lines into one paragraph.
        """

        nonlocal paragraph_lines

        if paragraph_lines:
            paragraph = " ".join(paragraph_lines).strip()

            if paragraph:
                blocks.append(paragraph)

            paragraph_lines = []

    for line in lines:

        # Preserve paragraph boundaries.
        if not line:
            flush_paragraph()
            continue

        # Keep headings, page markers, lists, and table rows.
        if is_structural_line(line):
            flush_paragraph()
            blocks.append(line)
            continue

        # Join wrapped lines belonging to a paragraph.
        paragraph_lines.append(line)

    # Add any remaining paragraph.
    flush_paragraph()

    # ------------------------------------------
    # 4. FORMAT CLEANED TEXT
    # ------------------------------------------

    cleaned_text = "\n\n".join(blocks)

    cleaned_text = MULTIPLE_BLANK_LINES.sub(
        "\n\n",
        cleaned_text,
    )

    return cleaned_text.strip()