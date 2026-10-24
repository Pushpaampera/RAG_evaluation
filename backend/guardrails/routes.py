from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.guardrails.service import (
    create_rule,
    delete_rule,
    list_rules,
    set_rule_enabled,
    update_rule,
)

router = APIRouter(
    prefix="/guardrails",
    tags=["Guardrails"],
)


GuardrailCategory = Literal[
    "input",
    "retrieval",
    "output",
    "scope",
    "safety",
    "ingestion",
]


class GuardrailCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1)
    category: GuardrailCategory
    rule_text: str = Field(min_length=1)
    enabled: bool = True


class GuardrailUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1)
    category: GuardrailCategory
    rule_text: str = Field(min_length=1)
    enabled: bool


class GuardrailStatusUpdate(BaseModel):
    enabled: bool


@router.get("/")
def get_guardrails():
    """Return all configured guardrail rules."""
    try:
        return {
            "success": True,
            "count": len(list_rules()),
            "rules": list_rules(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve guardrail rules.",
        ) from exc


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_guardrail(payload: GuardrailCreate):
    """Create a new guardrail rule."""
    try:
        rule = create_rule(
            name=payload.name.strip(),
            description=payload.description.strip(),
            category=payload.category,
            rule_text=payload.rule_text.strip(),
            enabled=payload.enabled,
        )

        return {
            "success": True,
            "message": "Guardrail created successfully.",
            "rule": rule,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create guardrail.",
        ) from exc


@router.put("/{rule_id}")
def edit_guardrail(rule_id: int, payload: GuardrailUpdate):
    """Update an existing guardrail rule."""
    try:
        rule = update_rule(
            rule_id=rule_id,
            name=payload.name.strip(),
            description=payload.description.strip(),
            category=payload.category,
            rule_text=payload.rule_text.strip(),
            enabled=payload.enabled,
        )

        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail rule not found.",
            )

        return {
            "success": True,
            "message": "Guardrail updated successfully.",
            "rule": rule,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update guardrail.",
        ) from exc


@router.patch("/{rule_id}/enabled")
def change_guardrail_status(
    rule_id: int,
    payload: GuardrailStatusUpdate,
):
    """Enable or disable a guardrail rule."""
    try:
        rule = set_rule_enabled(
            rule_id=rule_id,
            enabled=payload.enabled,
        )

        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail rule not found.",
            )

        return {
            "success": True,
            "message": (
                "Guardrail enabled successfully."
                if payload.enabled
                else "Guardrail disabled successfully."
            ),
            "rule": rule,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change guardrail status.",
        ) from exc


@router.delete("/{rule_id}")
def remove_guardrail(rule_id: int):
    """Delete a guardrail rule."""
    try:
        deleted = delete_rule(rule_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail rule not found.",
            )

        return {
            "success": True,
            "message": "Guardrail deleted successfully.",
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete guardrail.",
        ) from exc