import json
import logging

from pydantic import ValidationError
from backend.schemas import PostCallInsights

logger = logging.getLogger(__name__)


def extract_call_analysis(message: dict):

    artifact = message.get("artifact") or {}
    outputs = artifact.get("structuredOutputs") or {}

    if isinstance(outputs, dict):

        for output in outputs.values():

            if not isinstance(output, dict):
                continue

            result = output.get("result")

            if isinstance(result, str):

                try:
                    result = json.loads(result)

                except json.JSONDecodeError:
                    continue

            if not isinstance(result, dict):
                continue

            # Normalize field names
            result = {
                key.lower().strip(): value
                for key, value in result.items()
            }

            try:

                validated = PostCallInsights.model_validate(
                    result
                )

                logger.info(
                    "Structured call analysis extracted"
                )

                return validated.model_dump()

            except ValidationError as error:

                logger.warning(
                    "Structured analysis validation failed: %s",
                    error.error_count()
                )

    # Fallback if structured output is unavailable
    analysis = message.get("analysis") or {}

    return {
        "summary": analysis.get("summary"),
        "sentiment": "unknown",
        "objections": [],
        "next_action": None
    }