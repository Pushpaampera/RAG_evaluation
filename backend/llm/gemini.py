import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.rag.prompts import (
    SYSTEM_PROMPT,
    NOT_FOUND_MESSAGE,
    build_rag_prompt,
)

load_dotenv()

logger = logging.getLogger(__name__)


def generate_answer(
    question: str,
    retrieved_chunks: list[dict],
    history: list[dict] | None = None,
) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not retrieved_chunks:
        return NOT_FOUND_MESSAGE

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from the .env file.")

    prompt = build_rag_prompt(question, retrieved_chunks)

    contents = []

    for message in []:
        role = message.get("role")
        content = message.get("content")

        if role not in {"user", "assistant"}:
            continue

        if not isinstance(content, str) or not content.strip():
            continue

        contents.append(
            types.Content(
                role="user" if role == "user" else "model",
                parts=[types.Part.from_text(text=content)],
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    )

    models_to_try = [model_name]

    if fallback_model and fallback_model not in models_to_try:
        models_to_try.append(fallback_model)

    client = genai.Client(api_key=api_key)

    try:
        last_error = None

        for current_model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        
                    ),
                )

                answer = response.text

                if not answer or not answer.strip():
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                logger.info(
                    "Answer generated successfully using model %s.",
                    current_model,
                )

                return answer.strip()

            except Exception as error:
                last_error = error
                error_text = str(error).lower()

                temporary_error = any(
                    marker in error_text
                    for marker in (
                        "503",
                        "unavailable",
                        "high demand",
                        "overloaded",
                    )
                )

                if not temporary_error:
                    raise

                logger.warning(
                    "Gemini model %s is temporarily unavailable.",
                    current_model,
                )

        raise RuntimeError(
            "All configured Gemini models are temporarily unavailable."
        ) from last_error

    except Exception as error:
        logger.exception(f"Gemini answer generation failed.{error}")

        raise RuntimeError(
            f"Gemini could not generate an answer. Check model availability, "
            "API credentials, network connection, and API quota." 
        ) from error

    finally:
        client.close()