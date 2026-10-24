import re

MULTIPLE_SPACES = re.compile(r"[ \t]+")
MULTIPLE_BLANK_LINES = re.compile(r"\n{3,}")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s*(.+?)\s*#*\s*$")
LIST_PATTERN = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.+)$")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\|?[\s:|-]+\|?$")


def prepare_markdown(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    if not text.strip():
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    markdown_lines = []

    for line in lines:
        line = line.rstrip()

        if not line.strip():
            markdown_lines.append("")
            continue

        line = MULTIPLE_SPACES.sub(" ", line.strip())

        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            if heading_text:
                line = f"{'#' * level} {heading_text}"

        list_match = LIST_PATTERN.match(line)
        if list_match:
            indentation, marker, content = list_match.groups()
            line = f"{indentation}{marker} {content.strip()}"

        if TABLE_SEPARATOR_PATTERN.match(line) and "|" in line:
            line = line

        markdown_lines.append(line)

    markdown_text = "\n".join(markdown_lines)
    markdown_text = MULTIPLE_BLANK_LINES.sub("\n\n", markdown_text)

    return markdown_text.strip()