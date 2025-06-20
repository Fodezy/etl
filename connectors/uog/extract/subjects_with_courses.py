#!/usr/bin/env python3
# subjects_with_courses.py

import asyncio
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from .scrapper_modules.scrape_subjects_list import load_courses
from .parsers.subjects_with_courses_parser import parse_subjects_with_courses

# Max concurrent threads for scraping courses
MAX_WORKERS = 5

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


async def extract_and_parse_subjects(write_json: bool = True) -> dict:
    """
    Scrape subjects with courses, dump raw & cleaned JSON (if write_json=True),
    and return the cleaned data as a dict.
    """
    # 1) Load the subject catalog
    base_dir = Path(__file__).resolve().parent
    catalog_file = base_dir / 'data' / 'course_catalog' / 'course_catalog.json'
    if not catalog_file.exists():
        logger.error(f"Subject catalog not found at {catalog_file}")
        return {}

    logger.info(f"Stage 2: Loading subject catalog from {catalog_file}")
    subjects = json.loads(catalog_file.read_text(encoding='utf-8'))

    # 2) Scrape courses concurrently
    logger.info(f"Stage 2: Scraping {len(subjects)} subjects with {MAX_WORKERS} workers…")
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    async def fetch_subj(code: str, text: str):
        try:
            courses = await loop.run_in_executor(executor, load_courses, text)
            logger.info(f"  [{code}] Retrieved {len(courses)} courses")
        except Exception as e:
            logger.error(f"  [{code}] Error: {e}")
            courses = []
        return code, courses

    tasks = [fetch_subj(s['code'], s['text']) for s in subjects]
    pairs = await asyncio.gather(*tasks)
    executor.shutdown(wait=False)
    results = {code: courses for code, courses in pairs}

    # 3) Write raw intermediate output
    if write_json:
        raw_dir = base_dir / 'data' / 'course_catalog'
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / 'subjects_with_courses_raw.json'
        raw_file.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        logger.info(f"Stage 2: Saved raw courses to {raw_file}")

    # 4) Clean & normalize
    logger.info("Stage 2: Cleaning and normalizing course data…")
    cleaned = parse_subjects_with_courses(results)

    # 5) Write cleaned output only to connectors/uog/raw
    if write_json:
        cleaned_dir = base_dir.parent / 'raw'
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        clean_file = cleaned_dir / 'subjects_with_courses.json'
        clean_file.write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        logger.info(f"Stage 2: Saved cleaned courses to {clean_file}")

    return cleaned


if __name__ == '__main__':
    asyncio.run(extract_and_parse_subjects(write_json=True))
