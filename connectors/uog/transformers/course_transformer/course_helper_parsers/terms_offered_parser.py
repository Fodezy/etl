# transformer/course_transformer/course_helper_parsers/terms_offered_parser.py

import re
from typing import Dict, Any, Optional, List

# Define the keywords we are looking for based on the universal schema.
# This makes the parser easy to maintain.
SEASONS = ["Winter", "Spring", "Summer", "Fall"]
YEAR_PATTERNS = {
    "All Years": "All",
    "All": "All",
    "Even": "Even",
    "Odd": "Odd",
    "Annually": "Annually",
    "Biennially": "Biennially",
    "Triennially": "Triennially"
}

def parse_terms_offered(offered_string: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parses a raw 'offered' string into a structured list of OfferingPattern objects.

    Args:
        offered_string: The raw text from the source data (e.g., "Winter Only, All Years").

    Returns:
        A list containing a single structured OfferingPattern dictionary, or an empty list.
    """
    # 1. Handle edge cases where no offering info is available.
    if not offered_string or offered_string.strip().lower() == 'n/a':
        return []

    found_seasons = []
    found_years = []
    
    # Create a copy of the string to find the note later.
    note_text = offered_string

    # 2. Extract Seasons
    for season in SEASONS:
        if re.search(rf'\b{season}\b', offered_string, re.IGNORECASE):
            found_seasons.append(season)
            # Remove the found season from our note text copy
            note_text = re.sub(rf'\b{season}\b', '', note_text, flags=re.IGNORECASE)

    # 3. Extract Year Patterns
    for pattern_text, pattern_enum in YEAR_PATTERNS.items():
        if re.search(rf'\b{pattern_text}\b', offered_string, re.IGNORECASE):
            if pattern_enum not in found_years:
                found_years.append(pattern_enum)
            # Remove the found year pattern from our note text copy
            note_text = re.sub(rf'\b{pattern_text}\b', '', note_text, flags=re.IGNORECASE)

    # 4. Clean up the remaining text to create the note
    
    # --- FIX APPLIED HERE ---
    # The updated regex now uses word boundaries (\b) to only match the whole word 'and'.
    note_text = re.sub(r',|\band\b|&', '', note_text, flags=re.IGNORECASE)
    cleaned_note = note_text.strip() if note_text.strip() else None

    # 5. Construct the final object
    offering_pattern_obj = {
        "terms": found_seasons,
        "years": found_years,
        "note": cleaned_note
    }

    return [offering_pattern_obj]