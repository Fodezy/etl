# File: src/parse_prereq.py
# The main public entry point for the prerequisite parsing system.

import re
from typing import Any, Dict, List, Optional
from .parser.requisite_parser.parser import run_parser

# Pre-compiled regex to find and remove trailing commentary like "- Must be completed..."
# This is more efficient than compiling the regex on every function call.
DERAIL_PATTERN = re.compile(r"\s*[-–—]\s*Must\b.*", re.IGNORECASE)

def parse_prereq(raw_text: Optional[str], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Parses a raw prerequisite string into a list of structured JSON objects.
    """
    # 1. Trivial Rejection
    if not raw_text or raw_text.strip().lower() in ("", "none", "n/a"):
        return [{"type": "NO_REQUISITES", "chunk": ""}]

    # 2. **NEW**: Clean trailing commentary from the raw text before any splitting.
    cleaned_text = DERAIL_PATTERN.sub("", raw_text)

    # 3. Top-Level Split by Semicolon
    independent_chunks = cleaned_text.split(';')

    # 4. Dispatch each chunk to the core parser
    final_results = []
    for chunk in independent_chunks:
        stripped_chunk = chunk.strip()
        if stripped_chunk:
            parsed_chunk = run_parser(stripped_chunk, debug=debug)
            final_results.append(parsed_chunk)
    
    return final_results
