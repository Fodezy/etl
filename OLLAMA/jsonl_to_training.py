import json
import logging
from pathlib import Path # Import the Path object

# --- Configuration ---
# The final system prompt we developed.
SYSTEM_PROMPT = """You are an expert academic prerequisite parser. Your task is to transform a `raw_requisite` string into a single, valid JSON object conforming to the `RequisiteExpression` schema.

### Output Rules
- Output MUST be a single, valid JSON object ONLY. Do not include any conversational text, comments, or explanations.
- Strictly adhere to the `RequisiteExpression` schema: use exact `type` enum values and all required fields for each type.
- Handle ambiguity: Use `EQUIVALENT` for "or equivalent". Use `RAW_UNPARSED` for all other unparsable text (e.g., "permission of instructor").

### Core Parsing & Structural Rules
- Parentheses `()` and `[]` dictate logical grouping and take precedence.
- Commas `,` imply 'AND' at the same logical level.
- A sequence like "A, B or C" is parsed as `A AND (B OR C)`.
- `OR`/`N_OF` on a simple course list MUST use the `courses` array.
- `AND` or complex `OR`/`N_OF` (with nested logic or mixed types) MUST use the `expressions` array.
- `N_OF` requires a `count` field. Infer count from credit requirements (e.g., "1.00 credits from..." -> `"count": 2`).

### Schema: Type Definitions
The `type` field must be one of: "AND", "OR", "COURSE", "N_OF", "CREDITS", "PROGRAM_REGISTRATION", "SUBJECT_CREDITS_AT_LEVEL", "MIN_AVERAGE", "MIN_GRADE", "HIGHSCHOOL_REQUIREMENT", "MIN_EXPERIENCE", "PROGRESSION_STATUS", "PHASE_REQUIREMENT", "RAW_UNPARSED", "EXCLUDE_COURSE", "SUBJECT_CREDITS", "EQUIVALENT".

### Schema: Required Fields per Type
- `AND`: `expressions`
- `OR`: `expressions` OR `courses` (min 2 items)
- `COURSE`: `courses` (exactly 1 item)
- `N_OF`: `count`, and either `expressions` or `courses`
- `CREDITS`: `credits`
- `SUBJECT_CREDITS`: `credits`, `subject`
- `SUBJECT_CREDITS_AT_LEVEL`: `credits`, `subject`
- `MIN_AVERAGE`: `percentage`
- `MIN_GRADE`: `course`, `percentage`
- `PROGRAM_REGISTRATION`: `program`
- `PHASE_REQUIREMENT`: `phase`
- `HIGHSCHOOL_REQUIREMENT`: `description`
- `MIN_EXPERIENCE`: `description`
- `PROGRESSION_STATUS`: `description`
- `EXCLUDE_COURSE`: `courses`
- `RAW_UNPARSED`: `value`
- `EQUIVALENT`: `type` only

### Final Instruction
Parse the following string into one valid `RequisiteExpression` JSON:

Input: “{prerequisite_string}”
"""

# --- Script Logic ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def format_data_for_finetuning():
    """
    Reads the source data and converts it into the OpenAI JSONL format.
    """
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).resolve().parent
        
        # Define file paths relative to the script's directory
        input_file_path = script_dir / "Golden_DataSet_Final.jsonl"
        output_file_path = script_dir / "training_data.jsonl"

        logging.info(f"Reading from: {input_file_path}")
        logging.info(f"Writing to: {output_file_path}")

        with open(input_file_path, 'r', encoding='utf-8') as infile, \
             open(output_file_path, 'w', encoding='utf-8') as outfile:
            
            line_count = 0
            for line in infile:
                try:
                    source_data = json.loads(line)
                    user_content = source_data['raw_requisite']
                    assistant_content_obj = source_data['prerequisites']
                    assistant_content_str = json.dumps(assistant_content_obj, separators=(',', ':'))

                    training_example = {
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_content},
                            {"role": "assistant", "content": assistant_content_str}
                        ]
                    }

                    outfile.write(json.dumps(training_example) + '\n')
                    line_count += 1

                except (json.JSONDecodeError, KeyError) as e:
                    logging.error(f"Skipping line {line_count + 1} due to error: {e}. Offending line: {line.strip()}")

            logging.info(f"Successfully processed {line_count} lines.")
            logging.info(f"Output file '{output_file_path}' is ready for fine-tuning.")

    except FileNotFoundError:
        logging.error(f"Error: Input file could not be found at the expected path: {input_file_path}")

if __name__ == "__main__":
    format_data_for_finetuning()