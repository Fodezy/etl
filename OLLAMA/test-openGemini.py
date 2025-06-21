#!/usr/bin/env python3
# test_gemini_model.py

import os
import json
import logging
import requests  # Use the requests library for standard HTTP calls
from dotenv import load_dotenv

# --- Configuration ---
# 1. Configure logging to see the script's progress.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# 2. Set the model to Gemini Flash 2.0.
MODEL_ID = "gemini-2.0-flash"

# 3. The output file where the result will be saved.
OUTPUT_FILE_NAME = "gemini_api_test_output.json"

# 4. The restriction string to test.
USER_PROMPT = "Restricted to students in Culture and Technology Studies. This is a Priority Access Course. Enrolment may be restricted to particular programs or specializations. See department for more information"

# 5. A concise system prompt tailored for the Gemini API.
#    The entire prompt is sent as a single block of text.
SYSTEM_PROMPT = """You are a precise data extraction engine. Your sole task is to parse a `raw_restriction` string into a valid JSON object based on the `RequisiteExpression` schema.

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

Input: '{restriction_string}'"""

def test_gemini_model():
    """
    Sends a request to the Gemini API and saves the output to a JSON file.
    """
    try:
        # Load environment variables from a .env file
        load_dotenv()
        
        # Get your Gemini API key from environment variables
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            logger.error("Error: GEMINI_API_KEY is not set in your .env file or environment.")
            return

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={gemini_api_key}"
        
        # Construct the full prompt text for Gemini
        full_prompt = f"{SYSTEM_PROMPT}\n\nInput: \"{USER_PROMPT}\""

        # Construct the payload for the Gemini API
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }
        
        logger.info(f"Sending request to Gemini model: {MODEL_ID}")

        # Make the API call using the requests library
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        result = response.json()

        # Extract the JSON string from the Gemini API response structure
        json_string = result['candidates'][0]['content']['parts'][0]['text']

        if not json_string.strip():
            logger.error("API call succeeded but returned no content.")
            return

        logger.info("Successfully received response from API.")
        
        # Parse the JSON string into a Python dictionary
        parsed_json = json.loads(json_string)

        # Save the structured JSON to a file with pretty-printing
        with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully saved parsed output to '{OUTPUT_FILE_NAME}'")

    except requests.exceptions.RequestException as http_error:
        logger.error(f"HTTP Error during API call: {http_error}")
        logger.error(f"Response Body: {http_error.response.text}")
    except (KeyError, IndexError, json.JSONDecodeError) as parse_error:
        logger.error(f"Failed to parse the Gemini API response: {parse_error}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure the required Python libraries are installed
    try:
        import requests
        from dotenv import load_dotenv
    except ImportError:
        print("Required libraries are not installed.")
        print("Please install them by running: pip install requests python-dotenv")
        exit(1)
        
    test_gemini_model()
