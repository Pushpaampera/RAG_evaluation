import re
from dataclasses import dataclass
from typing import Literal


# 
# GUARDRAIL DECISION

Decision = Literal["ALLOW", "REJECT"]


@dataclass(frozen=True)
class GuardrailResult:
    decision: Decision
    stage: str
    reason: str

    @property
    def allowed(self) -> bool:
        return self.decision == "ALLOW"

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "stage": self.stage,
            "allowed": self.allowed,
            "reason": self.reason,
        }



# DOCUMENT SAFETY CONFIGURATION


MAX_DOCUMENT_CHARACTERS = 2_000_000



BLOCKED_DOCUMENT_PATTERNS = [
    re.compile(
        r"\bhow\s+to\s+build\s+a\s+bomb\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\binstructions\s+to\s+make\s+an\s+explosive\s+device\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bstep[- ]by[- ]step\s+instructions\s+to\s+poison\s+someone\b",
        re.IGNORECASE,
    ),
]



# DOCUMENT SAFETY CHECK


def check_document_safety(text: str) -> GuardrailResult:
    """
    Perform initial deterministic document safety checks.

    This function receives cleaned document text.

    It does not:
        - Generate embeddings.
        - Store data in PostgreSQL.
        - Call an LLM.
        - Replace PII masking.
        - Guarantee detection of every unsafe document.

    Returns:
        GuardrailResult containing ALLOW or REJECT.
    """

    
    # 1. VALIDATE INPUT
    

    if not isinstance(text, str):
        return GuardrailResult(
            decision="REJECT",
            stage="ingestion",
            reason="Document content must be text.",
        )

    if not text.strip():
        return GuardrailResult(
            decision="REJECT",
            stage="ingestion",
            reason="The document contains no readable text.",
        )

    
    # 2. CHECK DOCUMENT SIZE
    

    if len(text) > MAX_DOCUMENT_CHARACTERS:
        return GuardrailResult(
            decision="REJECT",
            stage="ingestion",
            reason=(
                "The document exceeds the permitted "
                "text-processing size."
            ),
        )

    
    # 3. CHECK CONFIGURED SAFETY PATTERNS
    

    for pattern in BLOCKED_DOCUMENT_PATTERNS:
        if pattern.search(text):
            return GuardrailResult(
                decision="REJECT",
                stage="ingestion",
                reason=(
                    "The document matched a configured "
                    "safety restriction."
                ),
            )

    
    # 4. ALLOW DOCUMENT
    

    return GuardrailResult(
        decision="ALLOW",
        stage="ingestion",
        reason="The document passed the configured checks.",
    )