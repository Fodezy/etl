# transformer/course_transformer/course_helper_parsers/section_parser.py

import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

def _parse_seats(seats_string: Optional[str]) -> Dict[str, Optional[int]]:
    """
    Parses a seats string like "66 / 250 / 0" into its components.
    Returns a dictionary with enrolled, capacity, and waitlist counts.
    """
    if not isinstance(seats_string, str):
        return {"enrolled": None, "capacity": None, "waitlist": None}
    
    parts = [p.strip() for p in seats_string.split('/')]
    try:
        return {
            "enrolled": int(parts[0]),
            "capacity": int(parts[1]),
            "waitlist": int(parts[2])
        }
    except (IndexError, ValueError):
        logger.warning(f"Could not parse seats string: '{seats_string}'")
        return {"enrolled": None, "capacity": None, "waitlist": None}

def _parse_instructors(instructor_string: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parses an instructor string which may contain multiple instructors.
    Example: "Senkl, D (Distance Education)\nIrvine, M (LEC)"
    """
    if not instructor_string or not isinstance(instructor_string, str):
        return []
    
    instructors = []
    # Split by newline for multiple instructors
    for line in instructor_string.strip().split('\n'):
        line = line.strip()
        if not line or line.lower() == 'n/a':
            continue
        
        # Regex to capture name and an optional role in parentheses
        match = re.match(r'^(.*?)\s*\((.*?)\)$', line)
        if match:
            name, role = match.groups()
            instructors.append({"name": name.strip(), "role": role.strip()})
        else:
            # If no role is specified, assume the whole string is the name
            instructors.append({"name": line, "role": None})
    return instructors

def _parse_meeting_time(day_time_string: Optional[str]) -> Dict[str, Any]:
    """
    Parses a complex day and time string into structured components.
    Example: "M,W,F 11:30 AM - 12:20 PM\n9/5/2025 - 8/1/2025"
    """
    if not day_time_string or 'TBD' in day_time_string:
        return {"days": [], "startTime": None, "endTime": None, "startDate": None, "endDate": None}
    
    parts = day_time_string.strip().split('\n')
    time_part = parts[0]
    date_part = parts[1] if len(parts) > 1 else ""

    # Day mapping to conform to schema
    day_map = {"M": "Mon", "T": "Tue", "W": "Wed", "TH": "Thu", "F": "Fri"}
    days = []
    # Match days like M, W, F or T,TH
    day_match = re.match(r'^[A-Z,]+', time_part)
    if day_match:
        day_str = day_match.group(0).replace(',', ' ').upper()
        # Handle "TH" before "T" to avoid incorrect matching
        if "TH" in day_str:
            days.append("Thu")
            day_str = day_str.replace("TH", "")
        for char in day_str:
            if char in day_map:
                days.append(day_map[char])

    # Time parsing with 12-hour to 24-hour conversion
    time_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', time_part)
    start_time, end_time = None, None
    if time_match:
        def to_24h(t_str):
            t_str = t_str.replace(' ', '').upper()
            hour, minute = map(int, t_str[:-2].split(':'))
            if 'PM' in t_str and hour != 12:
                hour += 12
            if 'AM' in t_str and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute:02d}"
        start_time = to_24h(time_match.group(1))
        end_time = to_24h(time_match.group(2))

    # Date parsing and formatting to YYYY-MM-DD
    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})', date_part)
    start_date, end_date = None, None
    if date_match:
        def to_iso(date_str):
            month, day, year = date_str.split('/')
            return f"{year}-{int(month):02d}-{int(day):02d}"
        start_date = to_iso(date_match.group(1))
        end_date = to_iso(date_match.group(2))

    return {"days": sorted(list(set(days))), "startTime": start_time, "endTime": end_time, "startDate": start_date, "endDate": end_date}

def parse_sections(source_sections: Optional[List[Dict]], course_code: str) -> List[Dict[str, Any]]:
    """
    The main orchestrator for parsing a list of sections for a course.
    """
    if not source_sections:
        return []

    universal_sections = []
    for section_data in source_sections:
        seats_info = _parse_seats(section_data.get("seats"))

        parsed_meetings = []
        all_instructors = []
        delivery_mode = "InPerson"  # Default

        for meeting_data in section_data.get("meetings", []):
            time_info = _parse_meeting_time(meeting_data.get("day_time"))
            location_string = meeting_data.get("location", "")
            
            # Infer meeting type from location string
            meeting_type = "Lecture"  # Default
            if "EXAM" in location_string: meeting_type = "Exam"
            elif "LAB" in location_string: meeting_type = "Lab"
            elif "TUT" in location_string: meeting_type = "Tutorial"

            # Infer delivery mode
            if "Distance Education" in location_string: delivery_mode = "Distance"
            
            all_instructors.extend(_parse_instructors(meeting_data.get("instructor")))
            
            parsed_meetings.append({
                "type": meeting_type,
                "dayOfWeek": time_info["days"],
                "startTime": time_info["startTime"],
                "endTime": time_info["endTime"],
                "startDate": time_info["startDate"],
                "endDate": time_info["endDate"],
                "location": location_string.split('\n')[0] # Take the first line as location
            })
        
        # Deduplicate instructors in case they are listed in multiple meetings
        unique_instructors = [dict(t) for t in {tuple(d.items()) for d in all_instructors}]

        universal_section = {
            "sectionId": section_data.get("section_code"),
            "courseCode": course_code, # Use the parent course code passed into the function
            "termId": "TBD",  # Term info is complex and will be derived later
            "sectionCode": section_data.get("section_code"),
            "status": "Open" if seats_info.get("enrolled", 0) < seats_info.get("capacity", 0) else "Closed",
            "capacity": seats_info.get("capacity"),
            "enrolled": seats_info.get("enrolled"),
            "waitlist": seats_info.get("waitlist"),
            "delivery": delivery_mode,
            "instructors": unique_instructors,
            "meetings": parsed_meetings
        }
        universal_sections.append(universal_section)

    return universal_sections

