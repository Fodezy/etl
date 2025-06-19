# File: ollama_parser.py
# Description: A robust parser using a pre-processing and substitution strategy.

import ollama
import json
import argparse
import sys, os
import re
from pathlib import Path
import pandas as pd
from typing import Any
from pydantic import ValidationError
import requests # This import is no longer strictly needed if OpenRouter is removed, but kept for potential future use or if other parts of your project use it.
from dotenv import load_dotenv
load_dotenv() 
import time
from google import genai

# --- Configuration ---
MAX_ATTEMPTS = 3

# IMPORTANT: genai.configure is removed as per user request to use genai.Client directly in the function.
# Ensure your GEMINI_API_KEY environment variable is set.
# Example: export GEMINI_API_KEY="YOUR_ACTUAL_API_KEY"


# --- Path Setup (Using your specified structure) ---
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
# CSV_PATH = SCRIPT_DIR / "courses_left.csv"

# --- Import Pydantic Models ---
try:
    from core.models.course import RequisiteExpression
except ImportError as e:
    print(f"❌ Error: Could not import Pydantic models from '{ETL_DIR}'.")
    print(f"   Please ensure the directory structure is 'etl/core/models/course.py'.")
    print(f"   Python Error: {e}")
    sys.exit(1)


def call_gemini_flash(prompt: str) -> dict:
    """
    Sends the full prompt to Google Gemini 2.0 Flash model using the genai.Client format.

    Args:
        prompt: The input text prompt for the model.

    Returns:
        A dictionary with the generated text, matching the shape of
        ollama.chat response for compatibility.
        Example: {"message": {"content": "Generated text goes here."}}
    """
    try:
        # Get the API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")

        # Initialize the client using genai.Client as requested
        client = genai.Client(api_key=api_key)

        # Generate content using client.models.generate_content as requested
        response = client.models.generate_content(
            # model="gemini-2.0-flash", 
            model="gemini-2.5-flash-lite-preview-06-17", 
            contents=prompt
        )

        # Return the generated text in the expected dictionary format
        return {"message": {"content": response.text}}
    except ValueError as ve:
        print(f"Configuration Error: {ve}")
        return {"message": {"content": f"Error: Configuration issue - {ve}"}}
    except Exception as e:
        print(f"An error occurred during Gemini text generation: {e}")
        # Return an error message in the expected format
        return {"message": {"content": f"Error: Could not generate text. {e}"}}


def _simplify_logical_container(node: dict) -> dict:
    """
    Recursively unwraps AND/OR containers that have only one expression,
    and collapses OR/N_OF expressions of simple COURSE types into a courses list.
    """
    # First, recursively process children
    if "expressions" in node and isinstance(node["expressions"], list):
        simplified_expressions = [
            _simplify_logical_container(expr) if isinstance(expr, dict) else expr
            for expr in node["expressions"]
        ]
        node["expressions"] = simplified_expressions

    # Rule 1: Unwrap AND/OR containers with only one expression
    if node.get("type") in ("AND", "OR") and len(node.get("expressions", [])) == 1:
        return _simplify_logical_container(node["expressions"][0]) # Recursively simplify the single child

    # Rule 2: Collapse OR/N_OF with expressions of simple COURSE types to courses list
    if node.get("type") in ("OR", "N_OF") and "expressions" in node and isinstance(node["expressions"], list):
        all_children_are_simple_courses = True
        collapsed_courses = []
        for expr in node["expressions"]:
            # Check if it's a simple COURSE type with a single course in its list
            if isinstance(expr, dict) and expr.get("type") == "COURSE" and \
               isinstance(expr.get("courses"), list) and len(expr["courses"]) == 1 and \
               isinstance(expr["courses"][0], str):
                collapsed_courses.append(expr["courses"][0])
            else:
                all_children_are_simple_courses = False
                break # Not all children are simple courses, so cannot collapse

        if all_children_are_simple_courses:
            # Create a new simplified node using the 'courses' array
            simplified_node = {"type": node["type"], "courses": collapsed_courses}
            if node["type"] == "N_OF": # N_OF also requires 'count'
                simplified_node["count"] = node["count"]
            # Remove expressions as we're switching to courses
            # del node["expressions"] # Not needed, we return a new node
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
    """Produce a short error message for logs."""
    max_len = 150
    if isinstance(e, ValidationError) and hasattr(e, 'errors') and e.errors():
        err = e.errors()[0]
        loc = ".".join(map(str, err.get('loc', [])))
        msg = err.get('msg', 'Unknown validation error')
        feedback = f"ValidationError at '{loc}': {msg}"
    else:
        feedback = f"{type(e).__name__}: {str(e).splitlines()[0]}"
    return feedback if len(feedback) <= max_len else feedback[:max_len-3] + "..."


def pre_parse_and_replace(text: str) -> tuple[str, dict]:
    """
    A simplified pre-parser that only handles basic, unambiguous patterns.
    This allows the LLM to handle complex sentences as intended by the prompt.
    """
    placeholder_map: dict[str, dict] = {}
    modified_text = text

    n_of_pattern = re.compile(r"(\(?\s*\d+\s+of\s+[A-Z\*0-9,\s]+\)?)", re.IGNORECASE)
    def n_of_replacer(m: re.Match) -> str:
        content = m.group(1)
        m2 = re.match(r"\s*(\d+)\s+of\s+(.+)", content, re.IGNORECASE)
        if m2:
            placeholder = f"__NODE_{len(placeholder_map)}__"
            count = int(m2.group(1))
            courses = [c.strip() for c in m2.group(2).split(',')]
            placeholder_map[placeholder] = {"type": "N_OF", "count": count, "courses": courses}
            return placeholder
        return m.group(0)
    modified_text = n_of_pattern.sub(n_of_replacer, modified_text)

    or_pattern = re.compile(r"\(\s*([A-Z]{2,}\*\d{4})\s+or\s+([A-Z]{2,}\*\d{4})\s*\)", re.IGNORECASE)
    def or_replacer(m: re.Match) -> str:
        placeholder = f"__NODE_{len(placeholder_map)}__"
        courses = [m.group(1).strip(), m.group(2).strip()]
        placeholder_map[placeholder] = {"type": "OR", "courses": courses}
        return placeholder
    modified_text = or_pattern.sub(or_replacer, modified_text)

    return modified_text, placeholder_map


def substitute_placeholders(node: Any, placeholder_map: dict[str, Any]) -> Any:
    """Recursively traverses the data structure and replaces placeholders."""
    if isinstance(node, str) and node in placeholder_map:
        return placeholder_map[node]
    if isinstance(node, dict):
        return {key: substitute_placeholders(value, placeholder_map) for key, value in node.items()}
    if isinstance(node, list):
        return [substitute_placeholders(item, placeholder_map) for item in node]
    return node


def parse_prerequisite(prereq_string: str, prompt_template: str) -> RequisiteExpression | None:
    """Robust parse with LLM and post-processing."""

    final_string_for_llm = prereq_string

    filled_prompt = prompt_template.replace("{prerequisite_string}", final_string_for_llm).strip()
    

    messages_history = [{"role": "system", "content": filled_prompt}]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"      ▶️  LLM Attempt {attempt}/{MAX_ATTEMPTS} for: '{final_string_for_llm[:75]}...'")
        try:
            # Call the Gemini Flash method
            response = call_gemini_flash(filled_prompt)

            json_string = response["message"]["content"]
            # # ─── DEBUG DUMP ───────────────────────────────────────────────
            # print("🛠️  [DEBUG] Raw LLM reply (json_string):")
            # print(json_string)
            # print("🛠️  [DEBUG] repr(json_string):")
            # print(repr(json_string))

            json_string = re.sub(r"^\s*```(?:json)?\s*", "", json_string)
            # Remove trailing ```
            json_string = re.sub(r"\s*```$", "", json_string)
            # Trim any leftover whitespace
            json_string = json_string.strip()
            messages_history.append({"role": "assistant", "content": json_string})
            data_dict = json.loads(json_string)

            validated = RequisiteExpression.model_validate(data_dict)
            result = validated.model_dump(mode="json", exclude_none=True)

            final_result = _simplify_logical_container(result)
            
            print(f"      ✅ Validation Successful on attempt {attempt}!")
            return RequisiteExpression.model_validate(final_result)

        except (ValidationError, json.JSONDecodeError, Exception) as e:
            err_msg = get_concise_error_message(e)
            print(f"      ❌ Attempt {attempt} failed. Error: {err_msg}")
            if attempt == MAX_ATTEMPTS:
                print(f"      ⚠️  Max attempts reached for '{prereq_string}'.")
                return None
            feedback = (
                f"Previous output failed validation: {err_msg}\n"
                f"Please re-parse *exactly*: \"{final_string_for_llm}\""
            )
            messages_history.append({"role": "user", "content": feedback})
        time.sleep(1.0)    # pause 1 second between courses
    return None
    

def main():
    parser = argparse.ArgumentParser(description="Parse course prerequisites from a CSV.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--num_courses", type=int, help="Number of random courses to process.")
    group.add_argument("-c", "--course_code", type=str, help="Specific course code to process.")
    parser.add_argument("-o", "--output", type=str, default="parsed_requisites.json", help="Output JSON file.")
    args = parser.parse_args()

    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        print(f"❌ CSV not found at '{CSV_PATH}'")
        sys.exit(1)

    df.dropna(subset=["requisites"], inplace=True)
    valid_df = df[df["requisites"].str.strip().str.lower() != "none"].copy()
    if valid_df.empty:
        print("ℹ️ No courses with prerequisites found.")
        sys.exit(0)

    prompt_template = load_prompt_template()
    final_results = []

    if args.course_code:
        courses_to_process = valid_df[
            valid_df["course_code"].str.strip().str.upper() == args.course_code.strip().upper()
        ]
        if courses_to_process.empty:
            print(f"❌ '{args.course_code}' not found or has no requisites.")
            sys.exit(1)
    else:
        n = min(args.num_courses, len(valid_df))
        print(f"Found {len(valid_df)} courses; processing random {n}.")
        courses_to_process = valid_df.sample(n=n)

    cleanup_pattern = re.compile(r'\s*-\s*Must be (?:completed|taken either) prior to.*$', re.IGNORECASE)
    recommendation_pattern = re.compile(r'\.\s*A grade average of.*?is recommended\.', re.IGNORECASE)

    for _, row in courses_to_process.iterrows():
        print("-" * 60)
        print(f"Processing Course: {row['course_code']}")
        clean_req = recommendation_pattern.sub('', row["requisites"]).strip()
        clean_req = cleanup_pattern.sub('', clean_req).strip()

        if not clean_req:
            continue

        if parsed_object := parse_prerequisite(clean_req, prompt_template):
            result = {
                "course_code": row["course_code"],
                "raw_requisite": row["requisites"],
                "prerequisites": parsed_object.model_dump(mode="json", exclude_none=True)
            }
            final_results.append(result)
        else:
            print(f"      Could not generate a valid structure for {row['course_code']}.")

    if final_results:
        out_path = SCRIPT_DIR / args.output
        print("-" * 60)
        print(f"Writing {len(final_results)} parsed prerequisites to '{out_path}'...")
        out_path.write_text(json.dumps(final_results, indent=2), encoding="utf-8")
        print("✅ Done.")
    else:
        print("No prerequisites parsed; nothing written.")


if __name__ == "__main__":
    main()
