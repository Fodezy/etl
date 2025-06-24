import os
import json
import logging
import re
from typing import Dict, Any, Optional

from openai import OpenAI

from core.utils.api_handler import handle_api_call, CircuitBreaker

# --- Module-level initializations ---
logger = logging.getLogger(__name__)

try:
    client = OpenAI()
    prereq_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    FINE_TUNED_MODEL_ID = os.environ.get("OPENAI_FINETUNED_MODEL_ID", "ft:gpt-3.5-turbo-0125:fodey::BkGY16gt")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client. Ensure OPENAI_API_KEY is set. Error: {e}")
    client = None
    prereq_circuit_breaker = None

SYSTEM_PROMPT = """
You are an expert academic prerequisite parser. Your task is to transform a `raw_requisite` string into a single, valid JSON object conforming to the `RequisiteExpression` schema.

### Output Rules
- Your response MUST be ONLY the valid JSON object. Do not include any conversational text or explanations.
- Every object you create must have a `"type"` key from the allowed list and all other fields required by the schema for that type.
- Use `EQUIVALENT` for "or equivalent" and `RAW_UNPARSED` for any other text that cannot be structured.

### Core Parsing Principles
- Parentheses `()` and brackets `[]` define logical groups and take precedence.
- Commas `,` at the same logical level imply an 'AND' relationship.
- For `OR` or `N_OF` on a simple list of courses, you MUST use the `courses` array. For complex or nested items, you MUST use the `expressions` array.
- For `N_OF`, the `count` field is required.

### Valid 'type' Values
The "type" field must be one of the following exact strings: "AND", "OR", "COURSE", "N_OF", "CREDITS", "PROGRAM_REGISTRATION", "SUBJECT_CREDITS_AT_LEVEL", "MIN_AVERAGE", "MIN_GRADE", "HIGHSCHOOL_REQUIREMENT", "MIN_EXPERIENCE", "PROGRESSION_STATUS", "PHASE_REQUIREMENT", "RAW_UNPARSED", "EXCLUDE_COURSE", "SUBJECT_CREDITS", "EQUIVALENT".

### Final Instruction
Parse the following string into one valid `RequisiteExpression` JSON:

Input: “{prerequisite_string}”
"""

# --- The dedicated, raw API call function ---
def _call_openai_api(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Makes the actual raw call to the OpenAI API.
    """
    if not client:
        raise ConnectionError("OpenAI client not initialized. Check API key.")

    response = client.chat.completions.create(
        model=payload["model"],
        messages=payload["messages"],
        temperature=payload["temperature"],
        response_format=payload["response_format"]
    )

    assistant_response_str = response.choices[0].message.content
    if assistant_response_str:
        return json.loads(assistant_response_str)
    else:
        raise ValueError("API response content was empty or None.")


# --- The main parser function ---
def parse_prerequisite_string(raw_prereq_text: str, course_code: str) -> Optional[Dict[str, Any]]:
    """
    Cleans the raw prerequisite string and then parses it into a structured
    JSON object by calling the fine-tuned model via the smart API handler.
    """
    if not raw_prereq_text or raw_prereq_text.strip().lower() == 'none':
        return None

    if not prereq_circuit_breaker:
        logger.error("Circuit breaker not initialized, cannot make API call.")
        return None

    # --- CLEANUP (from diff): Remove any trailing "- Must ..." suffix ---
    cleaned_text = re.sub(r'\s*-\s*Must\b.*$', '', raw_prereq_text, flags=re.IGNORECASE).strip()
    if not cleaned_text:
        # If nothing is left to parse after cleaning, return None.
        logger.debug(f"Prereq text for '{course_code}' was empty after cleaning.")
        return None
    
    # --- Construct the full prompt and payload using the cleaned text ---
    full_prompt = SYSTEM_PROMPT.format(prerequisite_string=cleaned_text)
    
    api_payload = {
        "model": FINE_TUNED_MODEL_ID,
        "messages": [
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    # Call the handler for caching, retries, etc.
    structured_prereqs = handle_api_call(
        api_function=_call_openai_api,
        payload=api_payload,
        circuit_breaker=prereq_circuit_breaker,
        parser_name="REQUISITE_PARSER",
        item_id=course_code
    )

    # Handle the final result
    if structured_prereqs:
        return structured_prereqs
    else:
        logger.warning(f"Could not parse prerequisite for '{course_code}' after all attempts.")
        # The fallback now uses the cleaned_text for more accurate logging of what failed.
        return {
            "type": "RAW_UNPARSED",
            "value": f"PARSING_FAILED: {cleaned_text}"
        }