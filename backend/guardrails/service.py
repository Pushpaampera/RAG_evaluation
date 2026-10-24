from backend.database.db import get_connection
from backend.guardrails.rules import (
    DEFAULT_GUARDRAIL_RULES,
    VALID_CATEGORIES,
)


def serialize_rule(row: tuple) -> dict:
    """Convert a PostgreSQL rule row into a JSON-friendly dictionary."""

    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "category": row[3],
        "rule_text": row[4],
        "enabled": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
        "updated_at": row[7].isoformat() if row[7] else None,
    }


def validate_rule(
    name: str,
    description: str,
    category: str,
    rule_text: str,
) -> None:
    """Validate rule fields before storing them."""

    if not name.strip():
        raise ValueError("Rule name cannot be empty.")

    if len(name.strip()) > 150:
        raise ValueError("Rule name cannot exceed 150 characters.")

    if not description.strip():
        raise ValueError("Rule description cannot be empty.")

    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category. Choose one of: "
            f"{', '.join(sorted(VALID_CATEGORIES))}."
        )

    if not rule_text.strip():
        raise ValueError("Rule instructions cannot be empty.")


def list_rules() -> list[dict]:
    """Return all guardrail rules, including disabled rules."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    category,
                    rule_text,
                    enabled,
                    created_at,
                    updated_at
                FROM guardrail_rules
                ORDER BY id;
                """
            )

            rows = cursor.fetchall()

    return [serialize_rule(row) for row in rows]


def get_active_rules(category: str | None = None) -> list[dict]:
    """Return enabled rules, optionally filtered by category."""

    if category is not None and category not in VALID_CATEGORIES:
        raise ValueError("Invalid guardrail category.")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            if category:
                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        description,
                        category,
                        rule_text,
                        enabled,
                        created_at,
                        updated_at
                    FROM guardrail_rules
                    WHERE enabled = TRUE AND category = %s
                    ORDER BY id;
                    """,
                    (category,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        description,
                        category,
                        rule_text,
                        enabled,
                        created_at,
                        updated_at
                    FROM guardrail_rules
                    WHERE enabled = TRUE
                    ORDER BY id;
                    """
                )

            rows = cursor.fetchall()

    return [serialize_rule(row) for row in rows]


def create_rule(
    name: str,
    description: str,
    category: str,
    rule_text: str,
    enabled: bool = True,
) -> dict:
    """Create and persist a guardrail rule."""

    validate_rule(name, description, category, rule_text)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO guardrail_rules (
                    name,
                    description,
                    category,
                    rule_text,
                    enabled
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING
                    id,
                    name,
                    description,
                    category,
                    rule_text,
                    enabled,
                    created_at,
                    updated_at;
                """,
                (
                    name.strip(),
                    description.strip(),
                    category,
                    rule_text.strip(),
                    enabled,
                ),
            )

            row = cursor.fetchone()

    return serialize_rule(row)


def update_rule(
    rule_id: int,
    name: str,
    description: str,
    category: str,
    rule_text: str,
    enabled: bool,
) -> dict | None:
    """Update a rule, returning None when its ID does not exist."""

    validate_rule(name, description, category, rule_text)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE guardrail_rules
                SET
                    name = %s,
                    description = %s,
                    category = %s,
                    rule_text = %s,
                    enabled = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING
                    id,
                    name,
                    description,
                    category,
                    rule_text,
                    enabled,
                    created_at,
                    updated_at;
                """,
                (
                    name.strip(),
                    description.strip(),
                    category,
                    rule_text.strip(),
                    enabled,
                    rule_id,
                ),
            )

            row = cursor.fetchone()

    return serialize_rule(row) if row else None


def set_rule_enabled(
    rule_id: int,
    enabled: bool,
) -> dict | None:
    """Enable or disable an existing rule."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE guardrail_rules
                SET
                    enabled = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING
                    id,
                    name,
                    description,
                    category,
                    rule_text,
                    enabled,
                    created_at,
                    updated_at;
                """,
                (enabled, rule_id),
            )

            row = cursor.fetchone()

    return serialize_rule(row) if row else None


def delete_rule(rule_id: int) -> bool:
    """Delete a rule. Return False if it does not exist."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM guardrail_rules
                WHERE id = %s
                RETURNING id;
                """,
                (rule_id,),
            )

            deleted_row = cursor.fetchone()

    return deleted_row is not None


def seed_default_rules() -> int:
    """
    Insert missing default rules without overwriting user changes.

    Returns the number of rules inserted.
    """

    inserted_count = 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for rule in DEFAULT_GUARDRAIL_RULES:
                cursor.execute(
                    """
                    INSERT INTO guardrail_rules (
                        name,
                        description,
                        category,
                        rule_text,
                        enabled
                    )
                    SELECT %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM guardrail_rules
                        WHERE name = %s
                    )
                    RETURNING id;
                    """,
                    (
                        rule["name"],
                        rule["description"],
                        rule["category"],
                        rule["rule_text"],
                        rule["enabled"],
                        rule["name"],
                    ),
                )

                if cursor.fetchone():
                    inserted_count += 1

    return inserted_count