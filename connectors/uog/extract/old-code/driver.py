#!/usr/bin/env python3
# driver.py

import asyncio
import logging as logger
from concurrent.futures import ThreadPoolExecutor

# ... (logging configuration and all run_* functions remain the same) ...

def run_course_catalog() -> list:
    """
    Stage 1: Scrape and parse the UoG course catalog subjects.
    """
    logger.info("→ Stage 1: course_catalog")
    from .course_catalog import extract_and_parse_course_catalog
    subjects = extract_and_parse_course_catalog(write_json=True)
    logger.info(f"✓ Stage 1 complete ({len(subjects)} subjects)")
    return subjects


def run_program_catalog() -> list:
    """
    Stage 3: Scrape and parse the UoG program catalog.
    """
    logger.info("→ Stage 3: program_catalog")
    from .program_catalog import extract_and_parse_program_catalog
    programs = asyncio.run(extract_and_parse_program_catalog(write_json=True))
    logger.info(f"✓ Stage 3 complete ({len(programs)} programs)")
    return programs


def run_subjects_with_courses() -> dict:
    """
    Stage 2: Extract, parse, and clean subjects with courses. --> not a full clean 
    """
    logger.info("→ Stage 2: subjects_with_courses")
    from .subjects_with_courses import extract_and_parse_subjects
    courses = asyncio.run(extract_and_parse_subjects(write_json=True))
    logger.info(f"✓ Stage 2 complete ({len(courses)} subjects)")
    return courses


def run_programs_with_sections() -> dict:
    """
    Stage 4: Extract, parse, and clean programs with sections. --> not a full clean 
    """
    logger.info("→ Stage 4: programs_with_sections")
    from .programs_with_sections import extract_and_parse_programs
    sections = asyncio.run(extract_and_parse_programs(write_json=True))
    logger.info(f"✓ Stage 4 complete ({len(sections)} programs)")
    return sections


def main() -> dict:
    """
    Orchestrates all four ETL stages in parallel and returns the
    final data payloads for the connector.
    """
    logger.info("Starting all four stages in parallel...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        # The catalog stages (1 & 3) still run to produce the
        # input files needed by the detail stages (2 & 4).
        future1 = executor.submit(run_course_catalog)
        future3 = executor.submit(run_program_catalog)

        # We must wait for the catalog stages to complete before starting the detail stages.
        # However, the detail stages can start as soon as their specific prerequisite is done.
        # A more advanced setup might use callbacks, but for simplicity, we'll wait for both.
        future1.result()
        future3.result()

        logger.info("Catalog stages complete. Starting detail stages...")
        future2 = executor.submit(run_subjects_with_courses)
        future4 = executor.submit(run_programs_with_sections)

        # Get the final results from the detail stages
        subjects_with_courses = future2.result()
        programs_with_sections = future4.result()

    logger.info("Pipeline complete.")

    # Return only the two dictionaries needed by the connector
    return {
        'subjects_with_courses': subjects_with_courses,
        'programs_with_sections': programs_with_sections
    }

if __name__ == '__main__':
    main()