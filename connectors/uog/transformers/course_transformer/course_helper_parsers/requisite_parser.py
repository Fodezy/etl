# transformer/course_transformer/course_helper_parsers/requisite_parser.py

import os
import json
import logging
from openai import OpenAI

client = OpenAI() 
logger = logging.getLogger(__name__)
# FINE_TUNED_MODEL_ID = "ft:gpt-3.5-turbo-0125:fodey::BkGY16gt" #openAI fine tuned modal api ID 
FINE_TUNED_MODEL_ID = "TEST"

def parse_prerequisite_string(raw_prereq_text: str) -> dict | None:
    """
    Parses a raw prerequisite string into a structured JSON object
    using the fine-tuned model.
    """
    # --- UPDATED CHECK ---
    # This now checks for None, empty strings, and the literal string 'None' (case-insensitive).
    if not raw_prereq_text or raw_prereq_text.strip().lower() == 'none':
        return None

    try:
        response = client.chat.completions.create(
            model=FINE_TUNED_MODEL_ID,
            messages=[
                {"role": "user", "content": raw_prereq_text}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        assistant_response_str = response.choices[0].message.content
        if assistant_response_str:
            structured_prereqs = json.loads(assistant_response_str)
            return structured_prereqs
        else:
            logger.warning(f"API response content was None for prerequisite: {raw_prereq_text}")
            return {
                "type": "RAW_UNPARSED",
                "value": f"PARSING_FAILED: Model returned no content for '{raw_prereq_text}'"
            }

    except Exception as e:
        logger.error(f"Failed to parse prerequisite string due to API error: {e}")
        logger.error(f"Offending prerequisite string: {raw_prereq_text}")
        return {
            "type": "RAW_UNPARSED",
            "value": f"PARSING_FAILED: {raw_prereq_text}"
        }