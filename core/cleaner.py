#!/usr/bin/env python3
"""
Universal raw data cleaner for extracted course JSONs.

Runs after extraction+parsing, normalizes common fields across schools
before the transformation stage.
"""
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


def parse_full_title(full_title: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Given a string like "ACCT*1240 Applied Financial Accounting (0.5 Credits)",
    return (code, name, credits).
    If it doesn’t match, fallback to splitting on first spaces.
    """
    if not full_title:
        return None, None, None
    pattern = r"^(\S+)\s+(.+?)\s*\(([^)]+)\)$"
    m = re.match(pattern, full_title)
    if m:
        return m.group(1), m.group(2), m.group(3)
    parts = full_title.split(" ", 2)
    code = parts[0] if len(parts) >= 1 else None
    name = parts[1] if len(parts) >= 2 else None
    credits = parts[2].strip("()\n") if len(parts) == 3 else None
    return code, name, credits


def clean_course(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean & normalize one course JSON dict, flattening the nested section structure.
    """
    cleaned: Dict[str, Any] = {}

    # 1) Split full_title
    full_title = raw.get("full_title")
    code, name, credits = parse_full_title(full_title)
    cleaned["code"] = code
    cleaned["name"] = name
    cleaned["credits"] = credits

    # 2) Simple string fields
    for field in ["description", "offerings", "restrictions", "departments", "requisites", "location", "offered"]:
        val = raw.get(field)
        if isinstance(val, str):
            cleaned[field] = val.strip() or None
        else:
            cleaned[field] = None
            
    # 3) --- FLATTEN NESTED SECTION STRUCTURE ---
    flattened_sections: List[Dict[str, Any]] = []
    # The top-level 'sections' in raw data is actually a list of term groupings.
    for term_group in raw.get("sections") or []:
        if not isinstance(term_group, dict):
            continue # Skip if an item in the list isn't a dictionary

        term_name = term_group.get("term_name")
        # The 'sections' key inside the term group contains the actual course sections.
        for section in term_group.get("sections") or []:
            if not isinstance(section, dict):
                continue # Skip if a nested item isn't a dictionary
            
            # Create a new, clean section dictionary
            clean_section = section.copy()

            # Promote the term_name into each individual section object
            clean_section['term'] = term_name
            
            # Use the unique section_code as the sectionId, providing a fallback
            clean_section['sectionId'] = section.get('section_code') or 'N/A'
            
            flattened_sections.append(clean_section)
    
    cleaned["sections"] = flattened_sections
    # --- END SECTION FLATTENING ---

    return cleaned


def clean_school(school_id: str) -> None:
    """
    Clean all JSON files under connectors/<school_id>/raw,
    writing outputs to connectors/<school_id>/clean (new directory).
    """
    root = Path(__file__).resolve().parent.parent
    raw_dir = root / "connectors" / school_id / "extract" / "raw"
    clean_dir = root / "connectors" / school_id / "extract" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)

    for src in raw_dir.glob("*.json"):
        raw = json.loads(src.read_text(encoding="utf-8"))
        cleaned = clean_course(raw)
        dest = clean_dir / src.name
        dest.write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: cleaner.py <school_id>")
        sys.exit(1)
    clean_school(sys.argv[1])