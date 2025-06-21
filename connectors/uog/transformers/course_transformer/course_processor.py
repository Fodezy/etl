# transformer/course_transformer/course_processor.py

import logging
import re
from typing import Dict, Any, Optional, List

# --- UPDATED IMPORTS ---
from .course_helper_parsers.requisite_parser import parse_prerequisite_string
from .course_helper_parsers.department_parser import parse_department
from .course_helper_parsers.terms_offered_parser import parse_terms_offered
from .course_helper_parsers.antirequisite_parser import parse_antirequisites
from .course_helper_parsers.program_restriction_parser import parse_program_restrictions # <-- NEW

logger = logging.getLogger(__name__)

# Other helper functions remain the same...
def _parse_credits_from_string(credit_string: Optional[str]) -> Optional[float]:
    if not isinstance(credit_string, str): return None
    match = re.search(r'\d+\.?\d*', credit_string)
    return float(match.group(0)) if match else None

def _parse_level_from_code(course_code: Optional[str]) -> Optional[int]:
    if not isinstance(course_code, str): return None
    match = re.search(r'\*(\d)', course_code)
    return int(match.group(1)) * 1000 if match else None

def _parse_sections(source_sections: Optional[List[Dict]]) -> List[Dict[str, Any]]:
    if not source_sections: return []
    return [{"sectionId": s.get("section_code"), "raw_data": s} for s in source_sections]


# --- MAIN WORKER FUNCTION ---

def process_single_course(source_course: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transforms a single source-clean course object into the universal schema.
    """
    try:
        course_code = source_course.get("code")
        
        # --- 1. Parse all fields independently ---
        
        # Parse course-based prerequisites from the 'requisites' field
        prereq_text = source_course.get("requisites")
        course_prereqs = parse_prerequisite_string(prereq_text)

        # Start processing the 'restrictions' field
        restrictions_text = source_course.get("restrictions")
        
        # --- 2. Implement the "Strip-and-Pass" logic ---
        
        # Step A: Parse for antirequisites first from the original string
        antireqs = parse_antirequisites(restrictions_text, course_code)
        
        # Step B: Filter the original string by removing the found antirequisites
        # This creates a cleaner string to send to the API
        filtered_restrictions = restrictions_text
        if antireqs and filtered_restrictions:
            for code in antireqs:
                # Use regex to remove the course code and potential following punctuation
                filtered_restrictions = re.sub(rf'\b{re.escape(code)}\b\s*[.,]?', '', filtered_restrictions).strip()

        # Step C: Parse the *filtered* string for program restrictions
        program_restrictions = parse_program_restrictions(filtered_restrictions)
        
        # --- 3. Intelligently combine prerequisite results ---
        final_prereqs = []
        if course_prereqs:
            final_prereqs.append(course_prereqs)
        if program_restrictions:
            final_prereqs.append(program_restrictions)

        if len(final_prereqs) > 1:
            prerequisite_obj = {"type": "AND", "expressions": final_prereqs}
        elif len(final_prereqs) == 1:
            prerequisite_obj = final_prereqs[0]
        else:
            prerequisite_obj = None

        # --- 4. Assemble the final universal course object ---
        universal_course = {
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
            "sections": _parse_sections(source_course.get("sections"))
        }

        logger.info(f"Successfully processed course: {universal_course['courseCode']}")
        return universal_course

    except Exception as e:
        course_code = source_course.get('code', 'UNKNOWN')
        logger.error(f"Failed to process course {course_code} due to error: {e}", exc_info=True)
        return None
