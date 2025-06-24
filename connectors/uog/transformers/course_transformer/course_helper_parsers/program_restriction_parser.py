import os
import json
import logging
import requests
from typing import Dict, Any, Optional

# --- NEW: Import the API handler and Circuit Breaker ---
from core.utils.api_handler import handle_api_call, CircuitBreaker

logger = logging.getLogger(__name__)

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-latest:generateContent?key={GEMINI_API_KEY}"
    # Each API gets its own circuit breaker instance
    restriction_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
else:
    logger.error("GEMINI_API_KEY environment variable not set. Restriction parser will be disabled.")
    GEMINI_API_URL = None
    restriction_circuit_breaker = None

# The prompt remains the same
RESTRICTION_SYSTEM_PROMPT = """You are a precise data extraction engine...""" # (keeping this collapsed for brevity)

# --- NEW: A dedicated, raw API call function using 'requests' ---
def _call_gemini_rest_api(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Makes the actual raw REST API call to Gemini.
    This function is what gets passed to the handle_api_call wrapper.
    It encapsulates all the 'requests' and response parsing logic.
    """
    if not GEMINI_API_URL:
        raise ConnectionError("Gemini API URL not configured. Check API key.")

    # The requests call and response parsing is moved here
    response = requests.post(GEMINI_API_URL, json=payload, timeout=60)
    response.raise_for_status()  # The handler will catch HTTP errors
    result = response.json()
    
    # Safely extract the JSON string from the nested response
    try:
        json_string = result['candidates'][0]['content']['parts'][0]['text']
        
        # If the model returns an empty string or empty JSON, it found no rules.
        if not json_string.strip() or json_string.strip() == '{}':
            return None
            
        parsed_json = json.loads(json_string)
        return parsed_json
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        # If the response structure is unexpected, raise an error for the handler
        logger.error(f"Failed to parse Gemini response structure: {e}")
        raise ValueError(f"Unexpected API response format: {result}") from e

# --- UPDATED: The main parser function, now much simpler ---
def parse_program_restrictions(restriction_text: str, course_code: str) -> Optional[Dict[str, Any]]:
    """
    Parses a 'restrictions' string by calling the Gemini model via the
    smart API handler, which manages caching, retries, and resiliency.
    """
    if not restriction_text or not restriction_text.strip() or not restriction_circuit_breaker:
        return None

    # 1. Prepare the payload for the API call
    full_prompt = RESTRICTION_SYSTEM_PROMPT.replace("{restriction_string}", restriction_text)
    api_payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }

    # 2. Call the handler for caching, retries, and circuit breaking
    structured_restrictions = handle_api_call(
        api_function=_call_gemini_rest_api,
        payload=api_payload,
        circuit_breaker=restriction_circuit_breaker,
        parser_name="RESTRICTION_PARSER",
        item_id=course_code
    )

    # 3. Handle the final result
    if structured_restrictions:
        return structured_restrictions
    else:
        # If the handler returns None, it means the call failed permanently or found no rules.
        # We can return None to signify no rule was found, or a fallback if needed.
        # For consistency, returning None is cleanest.
        logger.info(f"No structured restrictions found or parsing failed for '{course_code}'.")
        return None