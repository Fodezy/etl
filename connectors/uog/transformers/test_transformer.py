#!/usr/bin/env python3
# D:\CourseMap\etl\connectors\uog\transformers\test_transformer.py

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)
MAX_WORKERS = 10 # This will use up to 10 workers for the 10 courses

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR.parent / "raw" / "subjects_with_courses.json"
GOLDEN_PREREQS_PATH = BASE_DIR.parent.parent.parent / "OLLAMA" / "Golden_DataSet_Final.jsonl" # Corrected to .jsonl
OUTPUT_PATH = BASE_DIR / "test_output_universal_courses.json"


# --- Data Loading ---
# Using the line-by-line version that you confirmed works with your JSONL file.
def load_golden_prerequisites(path: Path) -> Dict[str, Any]:
    """Loads the pre-parsed prerequisites from a JSONL file into a lookup dictionary."""
    logger.info(f"Loading golden prerequisite data from: {path}")
    prereq_lookup = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                course_code = data.get("course_code")
                prereqs = data.get("prerequisites")
                if course_code:
                    prereq_lookup[course_code] = prereqs
    except FileNotFoundError:
        logger.error(f"Golden prerequisite file not found at {path}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode Golden prerequisite JSONL file: {e}")
    return prereq_lookup

def load_source_courses(path: Path) -> List[Dict[str, Any]]:
    """Loads the main source course data file and flattens it into a single list of courses."""
    logger.info(f"Loading source course data from: {path}")
    all_courses = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source_data_by_subject = json.load(f)
            for subject_courses in source_data_by_subject.values():
                all_courses.extend(subject_courses)
    except FileNotFoundError:
        logger.error(f"Source course data file not found at {path}")
    return all_courses

# --- Helper Parser Stubs ---
# (These functions remain the same)
def _parse_credits_from_string(credit_string: Optional[str]) -> Optional[float]:
    if not isinstance(credit_string, str): return None
    match = re.search(r'\d+\.?\d*', credit_string)
    return float(match.group(0)) if match else None

def _parse_level_from_code(course_code: Optional[str]) -> Optional[int]:
    if not isinstance(course_code, str): return None
    match = re.search(r'\*(\d)', course_code)
    return int(match.group(1)) * 1000 if match else None

def _parse_department(dept_string: Optional[str]) -> Optional[Dict[str, Any]]:
    if not dept_string: return None
    return {"deptId": f"dept_{dept_string.lower().replace(' ', '_')}", "name": dept_string}

def _parse_terms_offered(offered_string: Optional[str]) -> List[Dict[str, Any]]:
    if not offered_string: return []
    return [{"note": offered_string}]

def _parse_antirequisites(restrictions_string: Optional[str]) -> List[str]:
    if not restrictions_string: return []
    return re.findall(r'[A-Z]{2,5}\*\d{4}', restrictions_string)

def _parse_sections(source_sections: Optional[List[Dict]]) -> List[Dict[str, Any]]:
    if not source_sections: return []
    return [{"sectionId": s.get("section_code"), "raw_data": s} for s in source_sections]


# --- Modified Worker Function for Testing ---
def process_single_course_for_test(source_course: Dict[str, Any], prereq_lookup: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transforms a single course, getting prerequisites from the golden dataset lookup.
    """
    try:
        course_code = source_course.get("code")

        universal_course = {
            "courseId": course_code,
            "courseCode": course_code,
            "title": source_course.get("name"),
            "description": source_course.get("description"),
            "department": _parse_department(source_course.get("departments")),
            "level": _parse_level_from_code(course_code),
            "credits": _parse_credits_from_string(source_course.get("credits")),
            "prerequisites": None,
            "corequisites": None,
            "antirequisites": _parse_antirequisites(source_course.get("restrictions")),
            "crossListings": [],
            "tags": [],
            "termsOffered": _parse_terms_offered(source_course.get("offered")),
            "courseStatus": "Active",
            "sections": _parse_sections(source_course.get("sections"))
        }

        if course_code in prereq_lookup:
            universal_course['prerequisites'] = prereq_lookup[course_code]
        else:
            raw_req = source_course.get("requisites")
            if raw_req and raw_req.lower() != 'none':
                universal_course['prerequisites'] = {"type": "RAW_UNPARSED", "value": raw_req}

        return universal_course

    except Exception as e:
        logger.error(f"Failed to process item during test run: {e}. Item type: {type(source_course)}")
        return None

# --- Main Test Orchestration Logic ---
if __name__ == "__main__":
    all_source_courses = load_source_courses(RAW_DATA_PATH)
    golden_prereqs = load_golden_prerequisites(GOLDEN_PREREQS_PATH)

    if not all_source_courses:
        logger.error("No source courses loaded, exiting.")
    else:
        # --- MODIFICATION: Limit the number of courses to process ---
        test_batch_size = 2500
        courses_to_process = all_source_courses[:test_batch_size]
        logger.info(f"Limiting test run to the first {len(courses_to_process)} courses.")
        
        logger.info(f"Starting test transformation for {len(courses_to_process)} courses...")
        transformed_courses = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Pass the smaller, sliced list to the executor
            results_iterator = executor.map(lambda course: process_single_course_for_test(course, golden_prereqs), courses_to_process)

            for result in results_iterator:
                if result:
                    transformed_courses.append(result)

        logger.info(f"Successfully transformed {len(transformed_courses)} courses.")
        logger.info(f"Saving output to {OUTPUT_PATH}")
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(transformed_courses, f, indent=2, ensure_ascii=False)
        
        logger.info("Test run complete.")