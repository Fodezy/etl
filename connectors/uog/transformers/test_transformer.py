#!/usr/bin/env python3
# D:\CourseMap\etl\connectors\uog\transformers\test_transformer.py

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

# --- Import all real, implemented parsers ---
from course_transformer.course_helper_parsers.department_parser import parse_department
from course_transformer.course_helper_parsers.terms_offered_parser import parse_terms_offered
from course_transformer.course_helper_parsers.antirequisite_parser import parse_antirequisites
# We do NOT import the Gemini parser, as we will simulate its output below.

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)
MAX_WORKERS = 10

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR.parent / "raw" / "subjects_with_courses.json"
GOLDEN_PREREQS_PATH = BASE_DIR.parent.parent.parent / "OLLAMA" / "Golden_DataSet_Final.jsonl"
OUTPUT_PATH = BASE_DIR / "test_output_universal_courses.json"


# --- MOCK DATA FOR RESTRICTION PARSING ---
# This simulates the expected output of the Gemini API for known restriction patterns.
# The keys are the "filtered" strings after antirequisites have been removed.
GOLDEN_RESTRICTIONS = {
    "Restricted to students in Culture and Technology Studies. This is a Priority Access Course. Enrolment may be restricted to particular programs or specializations. See department for more information": {
        "type": "PROGRAM_REGISTRATION",
        "program": "Culture and Technology Studies"
    },
    "Restricted to students in BSCH.ABIO, BBRM.EQM, and BSAG majors/minor.": {
      "type": "OR",
      "expressions": [
        { "type": "PROGRAM_REGISTRATION", "program": "BSCH.ABIO" },
        { "type": "PROGRAM_REGISTRATION", "program": "BBRM.EQM" },
        { "type": "PROGRAM_REGISTRATION", "program": "BSAG majors/minor" }
      ]
    },
    "Instructor consent required.": {
        "type": "RAW_UNPARSED",
        "value": "Instructor consent required."
    }
    # Add other common restriction patterns here to test them.
}


# --- Data Loading ---
def load_golden_prerequisites(path: Path) -> Dict[str, Any]:
    """Loads the pre-parsed prerequisites from a JSONL file into a lookup dictionary."""
    logger.info(f"Loading golden prerequisite data from: {path}")
    prereq_lookup = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                prereq_lookup[data.get("course_code")] = data.get("prerequisites")
    except Exception as e:
        logger.error(f"Failed to load Golden Prerequisite file: {e}")
    return prereq_lookup

def load_source_courses(path: Path) -> List[Dict[str, Any]]:
    """Loads and flattens the source course data."""
    logger.info(f"Loading source course data from: {path}")
    all_courses = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source_data_by_subject = json.load(f)
            for subject_courses in source_data_by_subject.values():
                all_courses.extend(subject_courses)
    except Exception as e:
        logger.error(f"Failed to load source course data: {e}")
    return all_courses


# --- Local Helpers & Remaining Stubs ---
def _parse_credits_from_string(credit_string: Optional[str]) -> Optional[float]:
    if not isinstance(credit_string, str): return None
    match = re.search(r'\d+\.?\d*', credit_string)
    return float(match.group(0)) if match else None

def _parse_level_from_code(course_code: Optional[str]) -> Optional[int]:
    if not isinstance(course_code, str): return None
    match = re.search(r'\*(\d)', course_code)
    return int(match.group(1)) * 1000 if match else None

def _parse_sections(source_sections: Optional[List[Dict]]) -> List[Dict[str, Any]]:
    """(STUB) This remains a stub for now."""
    if not source_sections: return []
    return [{"sectionId": s.get("section_code"), "raw_data": s} for s in source_sections]


# --- UPDATED Worker Function for Testing ---
def process_single_course_for_test(source_course: Dict[str, Any], prereq_lookup: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transforms a single course, simulating the full logic for prerequisites and restrictions.
    """
    try:
        course_code = source_course.get("code")
        
        # --- 1. PARSE ALL PREREQUISITE & RESTRICTION SOURCES ---

        # Get course-based prereqs from the golden dataset (simulates OpenAI fine-tuned model)
        course_prereqs = prereq_lookup.get(course_code)

        # Get the full restrictions text
        restrictions_text = source_course.get("restrictions")
        
        # Parse the restrictions text for antirequisites first
        antireqs = parse_antirequisites(restrictions_text, course_code)
        
        # "Strip" the antirequisites from the string to create a cleaner version
        filtered_restrictions = restrictions_text
        if antireqs and filtered_restrictions:
            for code in antireqs:
                filtered_restrictions = re.sub(rf'\b{re.escape(code)}\b\s*[.,]?', '', filtered_restrictions).strip()
        
        # Simulate the Gemini API call by looking up the filtered string in our golden map
        program_restrictions = GOLDEN_RESTRICTIONS.get(filtered_restrictions)

        # --- 2. INTELLIGENTLY COMBINE PREREQUISITE RESULTS ---
        final_prereqs_list = []
        if course_prereqs:
            final_prereqs_list.append(course_prereqs)
        if program_restrictions:
            final_prereqs_list.append(program_restrictions)

        if len(final_prereqs_list) > 1:
            prerequisite_obj = {"type": "AND", "expressions": final_prereqs_list}
        elif len(final_prereqs_list) == 1:
            prerequisite_obj = final_prereqs_list[0]
        else:
            prerequisite_obj = None
        
        # --- 3. ASSEMBLE THE FINAL UNIVERSAL COURSE OBJECT ---
        universal_course = {
            "courseId": course_code,
            "courseCode": course_code,
            "title": source_course.get("name"),
            "description": source_course.get("description"),
            "department": parse_department(source_course.get("departments")),
            "level": _parse_level_from_code(course_code),
            "credits": _parse_credits_from_string(source_course.get("credits")),
            "prerequisites": prerequisite_obj, # This now contains the combined data
            "corequisites": None,
            "antirequisites": antireqs,
            "crossListings": [],
            "tags": [],
            "termsOffered": parse_terms_offered(source_course.get("offered")),
            "courseStatus": "Active",
            "sections": _parse_sections(source_course.get("sections"))
        }
        return universal_course

    except Exception as e:
        logger.error(f"Failed to process item during test run: {e}. Item: {source_course.get('code')}")
        return None

# --- Main Test Orchestration Logic ---
if __name__ == "__main__":
    all_source_courses = load_source_courses(RAW_DATA_PATH)
    golden_prereqs = load_golden_prerequisites(GOLDEN_PREREQS_PATH)

    if not all_source_courses:
        logger.error("No source courses loaded, exiting.")
    else:
        courses_to_process = all_source_courses[:2500]
        logger.info(f"Starting test transformation for {len(courses_to_process)} courses...")
        transformed_courses = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results_iterator = executor.map(lambda course: process_single_course_for_test(course, golden_prereqs), courses_to_process)
            for result in results_iterator:
                if result:
                    transformed_courses.append(result)

        logger.info(f"Successfully transformed {len(transformed_courses)} courses.")
        logger.info(f"Saving output to {OUTPUT_PATH}")
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(transformed_courses, f, indent=2, ensure_ascii=False)
        
        logger.info("Test run complete.")
