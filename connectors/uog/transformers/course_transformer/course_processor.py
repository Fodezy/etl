import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from pydantic import ValidationError
from core.models.course import UniversalCourseSchema

from .course_helper_parsers.requisite_parser import parse_prerequisite_string
from .course_helper_parsers.department_parser import parse_department
from .course_helper_parsers.terms_offered_parser import parse_terms_offered
from .course_helper_parsers.antirequisite_parser import parse_antirequisites
from .course_helper_parsers.program_restriction_parser import parse_program_restrictions
from .course_helper_parsers.section_parser import parse_sections
from .course_helper_parsers.description_parser import DescriptionParser

logger = logging.getLogger(__name__)

# ... (helper functions _parse_credits_from_string and _parse_level_from_code remain the same) ...
def _parse_credits_from_string(credit_string: Optional[str]) -> Optional[float]:
    if not isinstance(credit_string, str): return None
    match = re.search(r'\d+\.?\d*', credit_string)
    return float(match.group(0)) if match else None

def _parse_level_from_code(course_code: Optional[str]) -> Optional[int]:
    if not isinstance(course_code, str): return None
    match = re.search(r'\*(\d)', course_code)
    return int(match.group(1)) * 1000 if match else None


def process_single_course(
    source_course: Dict[str, Any],
    description_parser: DescriptionParser,
    requisite_cache: Dict[str, Any],
    restriction_cache: Dict[str, Any]
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Transforms a single source-clean course object into two final objects,
    utilizing in-memory caches to avoid reprocessing duplicate API calls.
    """
    course_code = source_course.get("code", "UNKNOWN")
    try:
        course_prereqs = None
        program_restrictions = None
        antireqs = None
        
        prereq_text = source_course.get("requisites")
        if prereq_text:
            if prereq_text in requisite_cache:
                course_prereqs = requisite_cache[prereq_text]
            else:
                course_prereqs = parse_prerequisite_string(prereq_text, course_code)
                requisite_cache[prereq_text] = course_prereqs
        
        restrictions_text = source_course.get("restrictions")
        if restrictions_text:
            antireqs = parse_antirequisites(restrictions_text, course_code)
            
            filtered_restrictions = restrictions_text
            if antireqs:
                for code in antireqs:
                    filtered_restrictions = re.sub(rf'\b{re.escape(code)}\b\s*[.,]?', '', filtered_restrictions).strip()

            if filtered_restrictions:
                if filtered_restrictions in restriction_cache:
                    program_restrictions = restriction_cache[filtered_restrictions]
                else:
                    program_restrictions = parse_program_restrictions(filtered_restrictions, course_code)
                    restriction_cache[filtered_restrictions] = program_restrictions
        
        description_text = source_course.get("description")
        description_data = {"embedding": [], "keywords": []}
        if description_text:
            description_data = description_parser.parse(description_text)
        extracted_tags = [kw["term"] for kw in description_data.get("keywords", [])]
        
        # --- DEBUGGING BLOCK ---
        logger.debug(f"--- Prereq Combination Logic for: {course_code} ---")
        logger.debug(f"Value of 'course_prereqs' before combining: {course_prereqs}")
        logger.debug(f"Value of 'program_restrictions' before combining: {program_restrictions}")
        # --- END DEBUGGING BLOCK ---
        
        final_prereqs = []
        if course_prereqs:
            final_prereqs.append(course_prereqs)

        if program_restrictions:
            # My previous logic was flawed. Let's log what happens with it.
            is_empty_unparsed = (
                program_restrictions.get("type") == "RAW_UNPARSED" and
                not program_restrictions.get("value")
            )
            logger.debug(f"Check 'is_empty_unparsed' for program_restrictions: {is_empty_unparsed}")
            if not is_empty_unparsed:
                logger.debug("Appending program_restrictions to final list.")
                final_prereqs.append(program_restrictions)
            else:
                logger.debug("Skipping append of program_restrictions.")
        
        if len(final_prereqs) > 1:
            prerequisite_obj = {"type": "AND", "expressions": final_prereqs}
        elif len(final_prereqs) == 1:
            prerequisite_obj = final_prereqs[0]
        else:
            prerequisite_obj = None

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

        validated_course = UniversalCourseSchema(**universal_course_dict)
        logger.info(f"Successfully processed and validated course: {validated_course.courseCode}")
        
        main_course_output = validated_course.model_dump(by_alias=True, mode='json', exclude_none=True)
        
        vector_data_output = {
            "id": course_code,
            "vector": description_data.get("embedding"),
            "payload": {"courseCode": course_code, "title": main_course_output.get("title")}
        }
        
        return main_course_output, vector_data_output

    except Exception as e:
        logger.error(f"Failed to process course {course_code} due to an unexpected error: {e}", exc_info=True)
        return None