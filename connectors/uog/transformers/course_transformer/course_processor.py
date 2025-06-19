# transformer/course_transformer/course_processor.py

import logging
import re
from typing import Dict, Any, Optional, List

# We will need the prerequisite parser from the other file
from .course_helper_parsers.requisite_parser import parse_prerequisite_string
from .course_helper_parsers.department_parser import parse_department

logger = logging.getLogger(__name__)




# leave
def _parse_credits_from_string(credit_string: Optional[str]) -> Optional[float]:
    """
    Extracts a number from a credit string like "0.5 Credits".
    """
    if not isinstance(credit_string, str):
        return None
    match = re.search(r'\d+\.?\d*', credit_string)
    if match:
        return float(match.group(0))
    return None

# leave
def _parse_level_from_code(course_code: Optional[str]) -> Optional[int]:
    """
    Infers the course level (e.g., 1000, 2000) from the course code.
    Example: "ACCT*1220" -> 1000
    """
    if not isinstance(course_code, str):
        return None
    match = re.search(r'\*(\d)', course_code)
    if match:
        return int(match.group(1)) * 1000
    return None

def _parse_terms_offered(offered_string: Optional[str]) -> List[Dict[str, Any]]:
    """
    (STUB) Parses the 'offered' string into a list of OfferingPattern objects.
    """
    if not offered_string:
        return []
    # Placeholder logic
    return [{
        "note": offered_string
    }]

def _parse_antirequisites(restrictions_string: Optional[str]) -> List[str]:
    """
    (STUB) Parses the 'restrictions' string to extract anti-requisite course codes.
    """
    if not restrictions_string:
        return []
    # This regex will find all course-like codes (e.g., ACCT*2220) in the string.
    return re.findall(r'[A-Z]{2,5}\*\d{4}', restrictions_string)

def _parse_sections(source_sections: Optional[List[Dict]]) -> List[Dict[str, Any]]:
    """
    (STUB) Parses the list of source sections into the universal schema format.
    """
    if not source_sections:
        return []
    
    universal_sections = []
    for section in source_sections:
        # Placeholder logic to map source section to universal section
        # This will eventually need its own helpers for meetings, instructors, etc.
        universal_section = {
            "sectionId": section.get("section_code"),
            "courseCode": section.get("section_name"), # This seems to be the course name in the source
            "termId": "TBD", # Term info would need to be passed in or derived
            "sectionCode": section.get("section_code"),
            # Further logic needed to parse status, capacity, meetings, etc.
        }
        universal_sections.append(universal_section)
    return universal_sections


# --- MAIN WORKER FUNCTION ---

def process_single_course(source_course: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transforms a single source-clean course object into the universal schema.
    """
    try:
        course_code = source_course.get("code")

        # This dictionary structure matches the universal_course.json schema.
        universal_course = {
            "courseId": course_code,
            "courseCode": course_code,
            "title": source_course.get("name"),
            "description": source_course.get("description"),
            "department": parse_department(source_course.get("departments")),
            "level": _parse_level_from_code(course_code),
            "credits": _parse_credits_from_string(source_course.get("credits")),
            "prerequisites": None,
            "corequisites": None,
            "antirequisites": _parse_antirequisites(source_course.get("restrictions")),
            "crossListings": [],
            "tags": [],

            # The 'offered' field from your source maps to 'termsOffered'
            "termsOffered": _parse_terms_offered(source_course.get("offered")),
            
            # Placeholder for course status
            "courseStatus": "Active",
            
            # The 'sections' field maps directly
            "sections": _parse_sections(source_course.get("sections"))
        }

        # --- Process Prerequisites using the fine-tuned model ---
        # The 'requisites' field from your source data is used here
        prereq_text = source_course.get("requisites")
        if prereq_text:
            structured_prereqs = parse_prerequisite_string(prereq_text)
            universal_course['prerequisites'] = structured_prereqs

        logger.info(f"Successfully processed course: {universal_course['courseCode']}")
        return universal_course

    except Exception as e:
        course_code = source_course.get('code', 'UNKNOWN')
        logger.error(f"Failed to process course {course_code} due to error: {e}")
        return None