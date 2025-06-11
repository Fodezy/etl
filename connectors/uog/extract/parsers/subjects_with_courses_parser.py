"""
subjects_with_courses_parser.py

Cleans and normalizes the raw subjects_with_courses data.
"""
from typing import Dict, List, Any


def parse_subjects_with_courses(raw: Dict[str, List[dict]]) -> Dict[str, List[dict]]:
    """
    Given raw mapping of subject_code -> list of course dicts,
    clean and normalize each course entry:
      - Remove entries missing required fields (code, name)
      - Strip whitespace from all string fields
      - Ensure sections have proper structure

    Returns cleaned mapping.
    """
    cleaned: Dict[str, List[dict]] = {}

    for subj_code, courses in raw.items():
        valid_courses: List[dict] = []
        for c in courses:
            # Required fields
            code = c.get('code', '') or ''
            name = c.get('name', '') or ''
            if not code.strip() or not name.strip():
                continue

            # Base course shape
            course = {
                'code': code.strip(),
                'name': name.strip(),
                'credits': (c.get('credits') or '').strip(),
                'description': (c.get('description') or '').strip(),
                'offerings': (c.get('offerings') or '').strip(),
                'restrictions': (c.get('restrictions') or '').strip(),
                'departments': (c.get('departments') or '').strip(),
                'requisites': (c.get('requisites') or '').strip(),
                'location': (c.get('location') or '').strip(),
                'offered': (c.get('offered') or '').strip(),
                'sections': []
            }

            # Clean sections
            raw_secs = c.get('sections') or []
            for sec in raw_secs:
                sec_code = (sec.get('section_code') or '').strip()
                sec_name = (sec.get('section_name') or '').strip()
                seats    = (sec.get('seats') or '').strip()
                # Build cleaned meetings list
                meetings: List[dict] = []
                for m in sec.get('meetings') or []:
                    day_time = (m.get('day_time') or '').strip()
                    dates    = (m.get('dates') or '').strip()
                    location = (m.get('location') or '').strip()
                    instr    = (m.get('instructor') or '').strip()
                    # Only include if there's at least a day/time
                    if day_time:
                        meetings.append({
                            'day_time': day_time,
                            'dates': dates,
                            'location': location,
                            'instructor': instr
                        })
                course['sections'].append({
                    'section_code': sec_code,
                    'section_name': sec_name,
                    'seats': seats,
                    'meetings': meetings
                })

            valid_courses.append(course)

        cleaned[subj_code] = valid_courses

    return cleaned
