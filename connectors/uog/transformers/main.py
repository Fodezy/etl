#!/usr/bin/env python3
# transformer/main.py

import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# --- Real Imports ---
# We now import the actual worker functions from the processor files.
from .course_transformer.course_processor import process_single_course
# The program processor will follow the same pattern once created.
# from .program_transformer.program_processor import process_single_program

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# This controls the number of concurrent API calls.
# It can be tuned based on the API's rate limits.
MAX_WORKERS = 10

# --- Main Orchestration Functions ---
# These functions now call the imported processors.

def transform_courses_universal(source_courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Orchestrates the parallel transformation of a list of source-clean courses.

    This function is designed to be called by an upstream connector.
    """
    logger.info(f"Starting universal transformation for {len(source_courses)} courses with {MAX_WORKERS} workers...")
    transformed_courses = []

    # The ThreadPoolExecutor now maps the REAL `process_single_course` function
    # from your course_processor.py file across all the source courses.
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results_iterator = executor.map(process_single_course, source_courses)

        for result in results_iterator:
            if result:
                transformed_courses.append(result)

    logger.info(f"Successfully transformed {len(transformed_courses)} out of {len(source_courses)} courses.")
    return transformed_courses


def transform_programs_universal(source_programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    (This will be functional once program_processor.py is created)
    Orchestrates the parallel transformation of a list of source-clean programs.
    """
    logger.info(f"Starting universal transformation for {len(source_programs)} programs with {MAX_WORKERS} workers...")
    transformed_programs = []

    # This part will work once you create program_processor.py and uncomment the import
    # with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    #     results_iterator = executor.map(process_single_program, source_programs)
    #     for result in results_iterator:
    #         if result:
    #             transformed_programs.append(result)

    logger.info(f"Successfully transformed {len(transformed_programs)} out of {len(source_programs)} programs.")
    return transformed_programs