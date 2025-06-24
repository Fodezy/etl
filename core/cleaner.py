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
from typing import Any, Dict, Tuple, Optional


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
    Clean & normalize one course JSON dict.
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

    # 3) Sections remain unchanged
    cleaned["sections"] = raw.get("sections", []) or []

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
        print(f"Cleaned {src.name} -> clean/{src.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: cleaner.py <school_id>")
        sys.exit(1)
    clean_school(sys.argv[1])
