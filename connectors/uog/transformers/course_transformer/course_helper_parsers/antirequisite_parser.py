# transformer/course_transformer/course_helper_parsers/antirequisite_parser.py

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# A constant for the course code pattern for reusability.
COURSE_CODE_REGEX = r'[A-Z]{2,5}\*\d{4}'

# A list of phrases that reliably indicate an antirequisite relationship,
# based on our analysis of the grouped_by_restrictions.json file.
ANTIREQUISITE_TRIGGERS = [
    "credit may be obtained for only one of",
    "credit will not be given for",
    "may not be taken for credit",
    "not available to students with credit in",
    "excluding"
]

def parse_antirequisites(restrictions_string: Optional[str], current_course_code: Optional[str]) -> List[str]:
    """
    Intelligently parses a restrictions string to extract only true
    antirequisite course codes. It first looks for a trigger phrase or
    pattern before extracting codes.

    Args:
        restrictions_string: The raw text from the source data's 'restrictions' field.
        current_course_code: The code of the course being processed, to exclude it from
                             the list of its own antirequisites.

    Returns:
        A list of course code strings identified as antirequisites, or an empty list.
    """
    if not restrictions_string or not current_course_code:
        return []

    lower_restrictions = restrictions_string.lower()
    trigger_found = False

    # 1. Check if any of our keyword trigger phrases are in the string.
    for trigger in ANTIREQUISITE_TRIGGERS:
        if trigger in lower_restrictions:
            trigger_found = True
            break
    
    # 2. If no keyword was found, check if the string STARTS with a course code.
    if not trigger_found:
        # re.match() only checks for a match at the beginning of the string.
        if re.match(COURSE_CODE_REGEX, restrictions_string):
            trigger_found = True
            
    # 3. If a trigger was found, extract all codes and filter them.
    if trigger_found:
        all_codes_found = re.findall(COURSE_CODE_REGEX, restrictions_string)
        
        # An antirequisite is any found course code that is not the current course.
        antireq_codes = [code for code in all_codes_found if code != current_course_code]
        
        if antireq_codes:
            logger.info(f"For {current_course_code}, found antirequisites: {antireq_codes}")
        return antireq_codes
    
    # 4. If no triggers were found, return an empty list, ignoring any other text.
    return []