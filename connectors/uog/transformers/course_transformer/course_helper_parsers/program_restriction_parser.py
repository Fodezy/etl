# transformer/course_transformer/course_helper_parsers/program_restriction_parser.py

# Need to switch over to the paid plan to use this in production- should be cheap overall though as small prompt + small input --> small ouput

import os
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# --- Configuration ---
# Your Gemini API Key should be stored securely as an environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# The concise, targeted prompt for parsing program/status restrictions.
RESTRICTION_SYSTEM_PROMPT = """You are a precise data extraction engine. Your sole task is to parse a `raw_restriction` string into a valid JSON object based on the `RequisiteExpression` schema.

### Core Rules:
1.  **JSON ONLY:** Your output MUST be a single, valid JSON object and nothing else.
2.  **Strict Schema:** Every object MUST have a `"type"` key. The other keys depend on the type.
    - For `AND`/`OR`, use an `"expressions"` key containing an array of objects.
    - For `PROGRAM_REGISTRATION`, use a `"program"` key.
    - For `RAW_UNPARSED`, use a `"value"` key.
3.  **Logical Grouping:** If a restriction lists multiple programs (e.g., "Restricted to A, B, and C"), you MUST group them in a nested `OR` expression.
4.  **No Rule, No Output:** If the input string contains only generic information (e.g., "Priority Access Course") and no specific rule, return an empty JSON object `{}`.

### Example of Correct Output Structure:
For an input like "Restricted to ProgramA and ProgramB. Instructor consent required.", the output MUST follow this nested structure:
`{"type":"AND", "expressions": [{"type":"OR", "expressions": [{"type":"PROGRAM_REGISTRATION", "program":"ProgramA"}, {"type":"PROGRAM_REGISTRATION", "program":"ProgramB"}]}, {"type":"RAW_UNPARSED", "value":"Instructor consent required."}]}`

### Final Instruction
Now, parse the following restriction string.

Input: “{restriction_string}”
"""


def parse_program_restrictions(restrictions_string: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Parses a 'restrictions' string for program or status-based rules
    using the Gemini Flash model.

    Args:
        restrictions_string: The raw text from the source data, ideally with antirequisites removed.

    Returns:
        A structured RequisiteExpression dictionary, or None if no rules are found.
    """
    if not restrictions_string or not restrictions_string.strip() or not GEMINI_API_KEY:
        return None

    full_prompt = f"{RESTRICTION_SYSTEM_PROMPT}\n\nInput: \"{restrictions_string}\""

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        json_string = result['candidates'][0]['content']['parts'][0]['text']
        
        if not json_string.strip() or json_string.strip() == '{}':
            return None
            
        parsed_json = json.loads(json_string)
        return parsed_json

    except requests.exceptions.RequestException as e:
        logger.error(f"API call to Gemini failed: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse Gemini response for input '{restrictions_string[:100]}...': {e}")
    
    return {"type": "RAW_UNPARSED", "value": f"RESTRICTION_PARSING_FAILED: {restrictions_string}"}
