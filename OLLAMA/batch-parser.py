# File: ollama_parser.py
# Description: A robust, rate-limited, and stateful pipeline for parsing course prerequisites.

import os
import sys
import json
import re
import time
from pathlib import Path
from typing import Any, List, Dict, Set

import pandas as pd
from pydantic import ValidationError
from dotenv import load_dotenv
from google import genai
from google.api_core import exceptions as google_exceptions

load_dotenv()

# --- Configuration ---
MAX_ATTEMPTS_PER_COURSE = 2
API_CALLS_PER_MINUTE = 12
RETRY_BASE_DELAY_SECONDS = 10  # Initial delay for exponential backoff

# --- Path Setup ---
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
    ETL_DIR = SCRIPT_DIR.parent
    if str(ETL_DIR) not in sys.path:
        sys.path.insert(0, str(ETL_DIR))
except NameError:
    ETL_DIR = Path.cwd()
    SCRIPT_DIR = ETL_DIR / "OLLAMA"

PROMPT_TEMPLATE_PATH = SCRIPT_DIR / "prompt-gen3.txt"
CSV_PATH = SCRIPT_DIR / "Course_Codes_and_Requisites.csv"

# Paths for state management and final output
PROCESSED_LOG_PATH = SCRIPT_DIR / "processed_courses.log"
FINAL_JSON_PATH = SCRIPT_DIR / "Golden_DataSet_Final.json"
FAILED_LOG_PATH = SCRIPT_DIR / "failed_courses.log"


# --- Import Pydantic Models ---
try:
    from core.models.course import RequisiteExpression
except ImportError as e:
    print(f"❌ Error: Could not import Pydantic models from '{ETL_DIR}'.")
    print("   Please ensure the directory structure is 'etl/core/models/course.py'.")
    print(f"   Python Error: {e}")
    sys.exit(1)


def call_gemini_flash(prompt: str) -> dict:
    """Sends the full prompt to the Google Gemini model."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17", 
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return {"message": {"content": response.text}}
    except ValueError as ve:
        print(f"Configuration Error: {ve}")
        return {"message": {"content": ""}, "error": str(ve)}
    except google_exceptions.ResourceExhausted as re_exc:
        raise re_exc
    except Exception as e:
        print(f"An error occurred during Gemini text generation: {e}")
        return {"message": {"content": ""}, "error": str(e)}


def _simplify_logical_container(node: dict) -> dict:
    """Recursively simplifies logical containers for consistency."""
    if "expressions" in node and isinstance(node["expressions"], list):
        node["expressions"] = [_simplify_logical_container(expr) for expr in node["expressions"]]

    if node.get("type") in ("AND", "OR") and len(node.get("expressions", [])) == 1:
        return _simplify_logical_container(node["expressions"][0])

    if node.get("type") in ("OR", "N_OF") and "expressions" in node:
        if all(expr.get("type") == "COURSE" and len(expr.get("courses", [])) == 1
               for expr in node["expressions"]):
            collapsed_courses = [expr["courses"][0] for expr in node["expressions"]]
            simplified_node = {"type": node["type"], "courses": collapsed_courses}
            if node["type"] == "N_OF":
                simplified_node["count"] = node["count"]
            return simplified_node
    return node


def load_prompt_template() -> str:
    """Loads the master prompt from the external text file."""
    try:
        return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"❌ Error: Prompt template not found at '{PROMPT_TEMPLATE_PATH}'")
        sys.exit(1)


def get_concise_error_message(e: Exception) -> str:
    """Produces a short, informative error message for logging."""
    if isinstance(e, ValidationError):
        err = e.errors()[0]
        loc = ".".join(map(str, err.get('loc', [])))
        return f"ValidationError at '{loc}': {err.get('msg', '')}"
    return f"{type(e).__name__}: {str(e).splitlines()[0]}"


def parse_prerequisite(prereq_string: str, prompt_template: str) -> RequisiteExpression | None:
    """
    Robustly parses a prerequisite string with LLM calls, validation, and retry logic.
    """
    filled_prompt = prompt_template.replace("{prerequisite_string}", prereq_string).strip()

    for attempt in range(1, MAX_ATTEMPTS_PER_COURSE + 1):
        try:
            print(f"      ▶️  LLM Attempt {attempt}/{MAX_ATTEMPTS_PER_COURSE}...")
            response = call_gemini_flash(filled_prompt)

            if response.get("error"):
                raise Exception(response["error"])

            json_string = response["message"]["content"].strip()
            if not json_string:
                raise json.JSONDecodeError("LLM returned an empty response.", "", 0)

            data_dict = json.loads(json_string)
            validated = RequisiteExpression.model_validate(data_dict)
            result = validated.model_dump(mode="json", exclude_none=True)
            final_result = _simplify_logical_container(result)

            print("      ✅ Validation Successful!")
            return RequisiteExpression.model_validate(final_result)

        except google_exceptions.ResourceExhausted as e:
            backoff_time = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            print(f"      RATE LIMIT HIT on attempt {attempt}. Waiting {backoff_time}s.")
            time.sleep(backoff_time)

        except (ValidationError, json.JSONDecodeError, Exception) as e:
            err_msg = get_concise_error_message(e)
            print(f"      ❌ Attempt {attempt} failed. Error: {err_msg}")
            if attempt < MAX_ATTEMPTS_PER_COURSE:
                time.sleep(1)
            continue

    return None


def load_processed_courses(path: Path) -> Set[str]:
    """Loads already processed course codes from the log file into a set."""
    if not path.exists():
        return set()
    with open(path, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}


def log_processed_items(items: List[str], path: Path):
    """Appends a list of processed items to the log file."""
    with open(path, 'a', encoding='utf-8') as f:
        for item in items:
            f.write(f"{item}\n")


def append_results_to_json(new_results: List[Dict], path: Path):
    """
    Reads the existing JSON file, appends new results, and writes it back
    with pretty-printing and sorted keys for manual verification.
    """
    existing_results = []
    if path.exists() and path.stat().st_size > 0:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: Output file '{path}' is corrupted. Starting fresh.")
            existing_results = []

    existing_results.extend(new_results)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(existing_results, f, indent=2, sort_keys=True)


def main():
    """Main execution pipeline for processing courses in rate-limited batches."""
    print("--- Starting Prerequisite Parsing Pipeline ---")

    prompt_template = load_prompt_template()
    processed_courses = load_processed_courses(PROCESSED_LOG_PATH)
    print(f"✅ Loaded {len(processed_courses)} previously processed courses from log.")

    try:
        df = pd.read_csv(CSV_PATH)
        df.dropna(subset=["requisites"], inplace=True)
        valid_df = df[df["requisites"].str.strip().str.lower() != "none"].copy()
    except FileNotFoundError:
        print(f"❌ Input CSV not found at '{CSV_PATH}'")
        sys.exit(1)

    courses_to_process_df = valid_df[~valid_df["course_code"].isin(processed_courses)]
    if courses_to_process_df.empty:
        print("✅ All courses have already been processed. Nothing to do.")
        sys.exit(0)

    print(f"▶️  Found {len(courses_to_process_df)} new courses to process.")

    to_do_list = courses_to_process_df.to_dict('records')
    total_to_process = len(to_do_list)
    processed_count = 0

    cleanup_pattern = re.compile(r'\s*-\s*Must be (?:completed|taken either) prior to.*$', re.IGNORECASE)

    while processed_count < total_to_process:
        batch_start_time = time.monotonic()
        batch_slice = to_do_list[processed_count: processed_count + API_CALLS_PER_MINUTE]

        print("-" * 70)
        print(f"Processing Batch: Courses {processed_count + 1} to {processed_count + len(batch_slice)} of {total_to_process}")
        print("-" * 70)

        batch_results = []
        failed_courses_in_batch = []

        for row in batch_slice:
            course_code = row['course_code']
            print(f"  > Processing Course: {course_code}")
            clean_req = cleanup_pattern.sub('', row["requisites"]).strip()

            if not clean_req:
                print("      - Skipping (empty requisite after cleanup).")
                continue

            if parsed := parse_prerequisite(clean_req, prompt_template):
                batch_results.append({
                    "course_code": course_code,
                    "raw_requisite": row["requisites"],
                    "prerequisites": parsed.model_dump(mode="json", exclude_none=True)
                })
            else:
                print(f"      ⚠️  Could not generate a valid structure for {course_code}. Logging as failed.")
                failed_courses_in_batch.append(course_code)

        if batch_results:
            print(f"\n  Batch complete. Appending {len(batch_results)} results to '{FINAL_JSON_PATH}'...")
            append_results_to_json(batch_results, FINAL_JSON_PATH)
            successful_codes = [res['course_code'] for res in batch_results]
            log_processed_items(successful_codes, PROCESSED_LOG_PATH)
            print(f"  ...Successfully logged {len(successful_codes)} courses.")
        if failed_courses_in_batch:
            log_processed_items(failed_courses_in_batch, FAILED_LOG_PATH)
            print(f"  ...Logged {len(failed_courses_in_batch)} failed courses.")

        processed_count += len(batch_slice)

        if processed_count < total_to_process:
            elapsed_time = time.monotonic() - batch_start_time
            pause_duration = max(0, 60.0 - elapsed_time)
            print(f"\n  Batch took {elapsed_time:.2f}s. Pausing for {pause_duration:.2f}s to respect rate limit...")
            time.sleep(pause_duration)

    print("\n--- Pipeline Complete ---")
    print("✅ All courses have been processed.")


if __name__ == "__main__":
    main()
