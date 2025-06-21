#!/usr/bin/env python3
# test_fine_tuned_model.py

import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration ---
# 1. Configure logging to see the script's progress.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# 2. Your fine-tuned model ID from the successful job.
MODEL_ID = "ft:gpt-3.5-turbo-0125:fodey::BkGY16gt"

# 3. The output file where the result will be saved.
OUTPUT_FILE_NAME = "api_test_output.json"

# 4. A sample prerequisite string to test the model.
USER_PROMPT = "12.50 credits including (1 of ANTH*3690, IDEV*2000, IDEV*2300, ONEH*3000), (1 of GEOG*2260, POLS*2650, IDEV*2100, SOAN*2120)"

# 5. A more concise system prompt optimized for a fine-tuned model.
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

def test_model():
    """
    Sends a request to the fine-tuned model and saves the output to a JSON file.
    """
    try:
        # Load environment variables from a .env file in the current directory
        load_dotenv()
        
        # Initialize the OpenAI client. It automatically uses the OPENAI_API_KEY
        # loaded from the .env file or the system environment.
        client = OpenAI()
        
        logger.info(f"Sending request to fine-tuned model: {MODEL_ID}")
        logger.info(f"Parsing prompt: '{USER_PROMPT}'")

        # Construct the API call
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT}
            ],
            temperature=0.0,  # Use 0.0 for deterministic, repeatable results
            response_format={"type": "json_object"}  # Enforce JSON output
        )

        # Extract the string content from the response
        assistant_response_str = response.choices[0].message.content

        if not assistant_response_str:
            logger.error("API call succeeded but returned no content.")
            return

        logger.info("Successfully received response from API.")
        
        # Parse the JSON string into a Python dictionary
        parsed_json = json.loads(assistant_response_str)

        # Save the structured JSON to a file with pretty-printing
        with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully saved parsed output to '{OUTPUT_FILE_NAME}'")

    except Exception as e:
        logger.error(f"An error occurred during the API call: {e}")

if __name__ == "__main__":
    # Check for required libraries before running
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("Required library 'python-dotenv' is not installed.")
        print("Please install it by running: pip install python-dotenv")
        exit(1)
        
    # Check for the API key
    load_dotenv()
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY not found.")
        print("Please create a .env file in this directory and add your key, e.g.:")
        print('OPENAI_API_KEY="sk-..."')
        exit(1)
        
    test_model()
