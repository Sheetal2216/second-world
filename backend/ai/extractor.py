
import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from core.config import settings
from schemas.world import WorldConfig


MAX_CHARS_PER_DATASET = 12000

SYSTEM_PROMPT = """
You are the AI World Builder for SECOND WORLD, a café decision-simulation platform.

Your task is to convert uploaded café business data into a structured WorldConfig.

RULES:
1. Use the supplied data as your source of truth. Never invent facts.
2. If required information is genuinely unavailable, use a reasonable,
   conservative estimate only when necessary for schema validation.
   Record every estimate in assumptions with its field_path and reason.
3. For unknown optional fields, use null and explain important gaps in
   missing_information.
4. Operating hours use decimal hours: 8.5 means 08:30.
5. Use INR as the default currency unless the data says otherwise.
6. Use sales and transaction data to estimate hourly customer arrivals
   only when the data supports that estimate. Do not confuse items sold
   with customer arrivals.
7. Menu prices must be positive. Do not invent menu items or prices.
8. Include all relevant available menu, staffing, inventory, operating
   hours, and customer-demand information.
9. popularity_share values, if provided for every menu item, must sum
   to approximately 1.
10. Return one JSON object matching the supplied JSON schema.
    Do not return Markdown or explanatory text outside the JSON.
"""


def build_context(datasets) -> str:
    """Prepare processed uploads for the AI, with a size limit per file."""
    parts = []

    for dataset in datasets:
        parsed_data = dataset.parsed_data or {}
        body = json.dumps(parsed_data, ensure_ascii=False, default=str)

        if len(body) > MAX_CHARS_PER_DATASET:
            body = body[:MAX_CHARS_PER_DATASET]
            body += "\n[Dataset content truncated due to size limit.]"

        parts.append(
            f"### Dataset ID: {dataset.id}\n"
            f"Filename: {dataset.filename}\n"
            f"File type: {dataset.file_type}\n"
            f"Content:\n{body}"
        )

    return "\n\n".join(parts)


def generate_world_config(datasets) -> WorldConfig:
    """Ask Gemini to build and validate a café WorldConfig."""

    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing from backend/.env"
        )

    if not settings.GEMINI_MODEL:
        raise ValueError(
            "GEMINI_MODEL is missing from backend/.env"
        )

    datasets = list(datasets)

    if not datasets:
        raise ValueError("No processed datasets were provided.")

    context = build_context(datasets)
    schema = json.dumps(WorldConfig.model_json_schema())

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"JSON SCHEMA:\n{schema}\n\n"
        f"CAFÉ BUSINESS DATA:\n{context}"
    )

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    last_error = None

    for attempt in range(2):
        current_prompt = prompt

        if last_error:
            current_prompt += (
                "\n\nYour previous JSON output failed validation. "
                "Correct these errors and return the complete JSON object:\n"
                f"{last_error}\n"
            )

        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            data = json.loads(response.text)

            # Always use the real database IDs, not IDs guessed by the AI.
            data["source_dataset_ids"] = [
                dataset.id for dataset in datasets
            ]

            return WorldConfig.model_validate(data)

        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = str(exc)[:2000]

    raise ValueError(
        "Gemini could not produce a valid WorldConfig after two attempts. "
        f"Last validation error: {last_error}"
    )
