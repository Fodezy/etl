# transformer/course_transformer/course_processor.py

import logging
import re
from typing import Dict, Any, Optional, List

# --- ADDED IMPORTS FOR VALIDATION ---
from pydantic import ValidationError
# Assuming the project root 'etl' is in the PYTHONPATH
# The path is relative from etl/ -> core/models/course.py
from etl.core.models.course import UniversalCourseSchema
# ------------------------------------

from .course_helper_parsers.requisite_parser import parse_prerequisite_string
from .course_helper_parsers.department_parser import parse_department
from .course_helper_parsers.terms_offered_parser import parse_terms_offered
from .course_helper_parsers.antirequisite_parser import parse_antirequisites
from .course_helper_parsers.program_restriction_parser import parse_program_restrictions
from .course_helper_parsers.section_parser import parse_sections

logger = logging.getLogger(__name__)

def _parse_credits_from_string(credit_string: Optional[str]) -> Optional[float]:
    if not isinstance(credit_string, str): return None
    match = re.search(r'\d+\.?\d*', credit_string)
    return float(match.group(0)) if match else None

def _parse_level_from_code(course_code: Optional[str]) -> Optional[int]:
    if not isinstance(course_code, str): return None
    match = re.search(r'\*(\d)', course_code)
    return int(match.group(1)) * 1000 if match else None

# --- MAIN WORKER FUNCTION (UPDATED) ---

def process_single_course(source_course: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transforms a single source-clean course object into the universal schema.
    Validates the transformed object against the Pydantic model before returning.
    """
    course_code = source_course.get("code", "UNKNOWN")
    try:
        # --- 1. Parse all fields independently ---
        # (Parsing logic remains the same)
        prereq_text = source_course.get("requisites")
        course_prereqs = parse_prerequisite_string(prereq_text)
        
        restrictions_text = source_course.get("restrictions")
        antireqs = parse_antirequisites(restrictions_text, course_code)
        
        filtered_restrictions = restrictions_text
        if antireqs and filtered_restrictions:
            for code in antireqs:
                filtered_restrictions = re.sub(rf'\b{re.escape(code)}\b\s*[.,]?', '', filtered_restrictions).strip()

        program_restrictions = parse_program_restrictions(filtered_restrictions)
        
        # --- 2. Intelligently combine prerequisite results ---
        # (Combining logic remains the same)
        final_prereqs = []
        if course_prereqs: final_prereqs.append(course_prereqs)
        if program_restrictions: final_prereqs.append(program_restrictions)

        if len(final_prereqs) > 1:
            prerequisite_obj = {"type": "AND", "expressions": final_prereqs}
        elif len(final_prereqs) == 1:
            prerequisite_obj = final_prereqs[0]
        else:
            prerequisite_obj = None

        # --- 3. Assemble the final universal course object ---
        universal_course_dict = {
            "courseId": course_code,
            "courseCode": course_code,
            "title": source_course.get("name"),
            "description": source_course.get("description"),
            "department": parse_department(source_course.get("departments")),
            "level": _parse_level_from_code(course_code),
            "credits": _parse_credits_from_string(source_course.get("credits")),
            "prerequisites": prerequisite_obj,
            "corequisites": None,
            "antirequisites": antireqs,
            "crossListings": [],
            "tags": [],
            "termsOffered": parse_terms_offered(source_course.get("offered")),
            "courseStatus": "Active",
            "sections": parse_sections(source_course.get("sections"), course_code)
        }

        # --- 4. VALIDATE AGAINST THE UNIVERSAL SCHEMA ---
        validated_course = UniversalCourseSchema(**universal_course_dict)
        
        logger.info(f"Successfully processed and validated course: {validated_course.courseCode}")
        
        # Return the validated data as a dictionary.
        # .model_dump() is for Pydantic v2. Use .dict() for v1.
        # by_alias=True is useful if your Pydantic model uses field aliases.
        return validated_course.model_dump(by_alias=True)

    except ValidationError as e:
        # This catches Pydantic-specific validation errors
        logger.error(
            f"Schema validation failed for course {course_code}. "
            f"See details below:\n{e}", 
            exc_info=False # Set to False because the validation error 'e' is very descriptive
        )
        return None
    
    except Exception as e:
        # This is the general catch-all for any other parsing errors
        logger.error(f"Failed to process course {course_code} due to an unexpected error: {e}", exc_info=True)
        return None