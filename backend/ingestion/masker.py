import re
from dataclasses import dataclass


@dataclass
class MaskingRule:
    name: str
    pattern: re.Pattern
    replacement: str
    enabled: bool = True


MASKING_RULES = [
    MaskingRule(
        name="EMAIL",
        pattern=re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        replacement="[EMAIL]",
    ),
    MaskingRule(
        name="API_KEY",
        pattern=re.compile(
            r"\b(?:api[_-]?key|access[_-]?token|"
            r"secret[_-]?key|client[_-]?secret)"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9_\-./+=]{12,}",
            re.IGNORECASE,
        ),
        replacement="[API_KEY]",
    ),
    MaskingRule(
        name="PASSWORD",
        pattern=re.compile(
            r"\b(?:password|passwd|pwd)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        replacement="[PASSWORD]",
    ),
    MaskingRule(
        name="TOKEN",
        pattern=re.compile(
            r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}",
            re.IGNORECASE,
        ),
        replacement="[TOKEN]",
    ),
]


PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:"
    r"\+\d{1,3}[\s.-]?\d(?:[\s.-]?\d){7,12}"
    r"|"
    r"\(?\d{3,5}\)?[\s.-]\d{3,5}[\s.-]\d{3,5}"
    r"|"
    r"[6-9]\d{9}"
    r")(?!\w)"
)

CARD_PATTERN = re.compile(
    r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)"
)


def is_valid_card_number(value: str) -> bool:
    digits = re.sub(r"\D", "", value)

    if not 13 <= len(digits) <= 19:
        return False

    total = 0

    for index, digit in enumerate(reversed(digits)):
        number = int(digit)

        if index % 2 == 1:
            number *= 2

            if number > 9:
                number -= 9

        total += number

    return total % 10 == 0


def mask_sensitive_data(text: str) -> dict:
    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    masked_text = text
    detected_categories = {}
    total_replacements = 0

    for rule in MASKING_RULES:
        if not rule.enabled:
            continue

        masked_text, count = rule.pattern.subn(
            rule.replacement,
            masked_text,
        )

        if count:
            detected_categories[rule.name] = (
                detected_categories.get(rule.name, 0) + count
            )
            total_replacements += count

    masked_text, phone_count = PHONE_PATTERN.subn(
        "[PHONE]",
        masked_text,
    )

    if phone_count:
        detected_categories["PHONE"] = phone_count
        total_replacements += phone_count

    def replace_card(match):
        nonlocal total_replacements

        value = match.group(0)

        if not is_valid_card_number(value):
            return value

        total_replacements += 1
        detected_categories["CARD_NUMBER"] = (
            detected_categories.get("CARD_NUMBER", 0) + 1
        )

        return "[CARD_NUMBER]"

    masked_text = CARD_PATTERN.sub(
        replace_card,
        masked_text,
    )

    return {
        "masked_text": masked_text,
        "detected_categories": detected_categories,
        "total_replacements": total_replacements,
    }


def configure_masking_rule(name: str, enabled: bool) -> bool:
    for rule in MASKING_RULES:
        if rule.name == name:
            rule.enabled = enabled
            return True

    return False