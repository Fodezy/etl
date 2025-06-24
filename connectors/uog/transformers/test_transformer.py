#!/usr/bin/env python3
# D:\CourseMap\etl\connectors\uog\transformers\test_transformer.py

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# --- Import all real, implemented parsers ---
from .course_transformer.course_helper_parsers.department_parser import parse_department
from .course_transformer.course_helper_parsers.terms_offered_parser import parse_terms_offered
from .course_transformer.course_helper_parsers.antirequisite_parser import parse_antirequisites
from .course_transformer.course_helper_parsers.section_parser import parse_sections
# --- NEW: Import the real DescriptionParser ---
from .course_transformer.course_helper_parsers.description_parser import DescriptionParser

from pydantic import ValidationError
from core.models.course import UniversalCourseSchema

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
COURSE_OUTPUT_PATH = BASE_DIR / "test_output_universal_courses.json"
VECTOR_OUTPUT_PATH = BASE_DIR / "test_output_universal_vectors.json"


# --- DELETED: The MOCK_DESCRIPTION_DATA block is no longer needed. ---


# --- MOCK DATA FOR RESTRICTION PARSING ---
# We still mock the Gemini API call for restrictions
GOLDEN_RESTRICTIONS = {
    "Restricted to students in Culture and Technology Studies. This is a Priority Access Course. Enrolment may be restricted to particular programs or specializations. See department for more information": {
        "type": "PROGRAM_REGISTRATION",
        "program": "Culture and Technology Studies"
    },
    # ... other golden restrictions
}


# --- Data Loading (No changes here) ---
def load_golden_prerequisites(path: Path) -> Dict[str, Any]:
    # ... function remains the same
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
    # ... function remains the same
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


# --- Local Helpers (No changes here) ---
def _parse_credits_from_string(credit_string: Optional[str]) -> Optional[float]:
    # ... function remains the same
    if not isinstance(credit_string, str): return None
    match = re.search(r'\d+\.?\d*', credit_string)
    return float(match.group(0)) if match else None

def _parse_level_from_code(course_code: Optional[str]) -> Optional[int]:
    # ... function remains the same
    if not isinstance(course_code, str): return None
    match = re.search(r'\*(\d)', course_code)
    return int(match.group(1)) * 1000 if match else None


# --- UPDATED Worker Function for Testing ---
# It now accepts the real parser instance.
def process_single_course_for_test(
    source_course: Dict[str, Any], 
    prereq_lookup: Dict[str, Any],
    description_parser: DescriptionParser
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Transforms a single course, simulating LLM calls but running the real
    description parser to generate actual embeddings and tags.
    """
    course_code = source_course.get("code", "UNKNOWN")
    try:
        # --- 1. SIMULATE & REAL PARSING LOGIC ---
        # (Prereq and restriction logic remains simulated)
        course_prereqs = prereq_lookup.get(course_code)
        restrictions_text = source_course.get("restrictions")
        antireqs = parse_antirequisites(restrictions_text, course_code)
        
        filtered_restrictions = restrictions_text or ""
        if antireqs and filtered_restrictions:
            for code in antireqs:
                filtered_restrictions = re.sub(rf'\b{re.escape(code)}\b\s*[.,]?', '', filtered_restrictions).strip()
        
        program_restrictions = GOLDEN_RESTRICTIONS.get(filtered_restrictions)
        
        # Call the REAL description parser
        description_text = source_course.get("description") or ""
        description_data = description_parser.parse(description_text)
        extracted_tags = [kw["term"] for kw in description_data.get("keywords", [])]

        # --- 2. COMBINE PREREQUISITE RESULTS ---
        final_prereqs_list = []
        if course_prereqs: final_prereqs_list.append(course_prereqs)
        if program_restrictions: final_prereqs_list.append(program_restrictions)

        if len(final_prereqs_list) > 1:
            prerequisite_obj = {"type": "AND", "expressions": final_prereqs_list}
        elif len(final_prereqs_list) == 1:
            prerequisite_obj = final_prereqs_list[0]
        else:
            prerequisite_obj = None
        
        # --- 3. ASSEMBLE THE FINAL OBJECT (WITH ALL FIELDS RESTORED) ---
        universal_course_dict = {
            "courseId": course_code,
            "courseCode": course_code,
            "title": source_course.get("name"),
            "description": source_course.get("description"),
            "department": parse_department(source_course.get("departments")),
            "level": _parse_level_from_code(course_code),
            "credits": _parse_credits_from_string(source_course.get("credits")) or 0.0,
            "prerequisites": prerequisite_obj,
            "corequisites": None,
            "antirequisites": antireqs,
            "crossListings": [],
            "tags": extracted_tags,
            "termsOffered": parse_terms_offered(source_course.get("offered")),
            "courseStatus": "Active",
            "sections": parse_sections(source_course.get("sections"), course_code)
        }

        # --- 4. VALIDATE & PREPARE OUTPUTS ---
        validated_course = UniversalCourseSchema(**universal_course_dict)
        main_course_output = validated_course.model_dump(mode='json', by_alias=True)
        vector_data_output = {
            "id": course_code,
            "vector": description_data["embedding"],
            "payload": {"courseCode": course_code, "title": main_course_output.get("title")}
        }
        return main_course_output, vector_data_output

    except ValidationError as e:
        logger.error(
            f"Schema validation failed for course {course_code} during test run. "
            f"Details:\n{e}", 
            exc_info=False
        )
        return None
    except Exception as e:
        logger.error(f"Failed to process item {course_code} during test run due to an unexpected error: {e}", exc_info=True)
        return None

# --- Main Test Orchestration Logic (UPDATED) ---
if __name__ == "__main__":
    all_source_courses = load_source_courses(RAW_DATA_PATH)
    golden_prereqs = load_golden_prerequisites(GOLDEN_PREREQS_PATH)

    if not all_source_courses:
        logger.error("No source courses loaded, exiting.")
    else:
        # --- NEW: Initialize the real parser ONCE before the threads start ---
        # This will take a moment as it loads the ML models into memory.
        description_parser = DescriptionParser()

        courses_to_process = all_source_courses[:25] # Using a smaller number for a quicker real test
        logger.info(f"Starting REAL transformation for {len(courses_to_process)} courses...")
        
        transformed_courses = []
        vector_data_points = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # --- UPDATED: Pass the description_parser instance to the worker ---
            results_iterator = executor.map(
                lambda course: process_single_course_for_test(course, golden_prereqs, description_parser), 
                courses_to_process
            )
            for result in results_iterator:
                if result:
                    main_course, vector_point = result
                    transformed_courses.append(main_course)
                    vector_data_points.append(vector_point)

        logger.info(f"Successfully transformed {len(transformed_courses)} courses.")
        
        # --- Save both output files (No changes here) ---
        logger.info(f"Saving main course data to {COURSE_OUTPUT_PATH}")
        with open(COURSE_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(transformed_courses, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saving vector data to {VECTOR_OUTPUT_PATH}")
        with open(VECTOR_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(vector_data_points, f, indent=2, ensure_ascii=False)
        
        logger.info("Test run complete.")