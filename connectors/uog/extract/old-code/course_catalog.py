#!/usr/bin/env python3
# course_catalog.py

import json
import logging
from pathlib import Path

from .scrapper_modules.scrape_subjects_list import load_subjects, parse_subjects

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def extract_and_parse_course_catalog(write_json: bool = True) -> list:
    """
    Stage 1: Scrape and parse the UofG course catalog subjects.
    Optionally writes JSON output and returns the parsed list.

    Args:
        write_json (bool): If True, write the catalog JSON to disk.

    Returns:
        List[dict]: Parsed subjects with keys 'code', 'name', 'text'.
    """
    logger.info("Stage 1: Loading raw subjects from the UofG Courses page...")
    raw_subjects = load_subjects()

    logger.info(f"Stage 1: Retrieved {len(raw_subjects)} raw subjects; parsing...")
    subjects = parse_subjects(raw_subjects)

    if write_json:
        base_dir = Path(__file__).resolve().parent
        output_dir = base_dir / 'data' / 'course_catalog'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / 'course_catalog.json'

        logger.info(f"Stage 1: Writing parsed subjects ({len(subjects)}) to {output_file}")
        output_file.write_text(
            json.dumps(subjects, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    return subjects


if __name__ == '__main__':
    # Run stage 1 with JSON dump
    extract_and_parse_course_catalog(write_json=True)
