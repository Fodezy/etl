#!/usr/bin/env python3
# transformer/main.py

import logging
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

# --- Real Imports ---
from .course_transformer.course_processor import process_single_course
from .course_transformer.course_helper_parsers.description_parser import DescriptionParser
# from .program_transformer.program_processor import process_single_program

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)
MAX_WORKERS = 10

# --- Main Orchestration Functions ---

def transform_courses_universal(
    source_courses: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Orchestrates the parallel transformation of source-clean courses.

    This function initializes all necessary singleton objects (like parsers
    with ML models and in-memory caches) and passes them to the worker threads.
    """
    logger.info(f"Starting universal transformation for {len(source_courses)} courses with {MAX_WORKERS} workers...")
    
    main_course_objects = []
    vector_data_points = []

    # --- INITIALIZE SINGLETONS AND SHARED OBJECTS ---
    # 1. Initialize the parser with ML models so they are loaded only once.
    description_parser = DescriptionParser()
    
    # 2. Initialize the in-memory caches. These dictionaries will be shared
    #    across all threads to prevent reprocessing duplicate strings.
    requisite_in_memory_cache: Dict[str, Any] = {}
    restriction_in_memory_cache: Dict[str, Any] = {}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # --- UPDATED: The lambda now passes the shared caches to the worker ---
        # Each call to process_single_course gets the same parser and cache objects.
        results_iterator = executor.map(
            lambda course: process_single_course(
                course, 
                description_parser,
                requisite_in_memory_cache,
                restriction_in_memory_cache
            ), 
            source_courses
        )

        for result in results_iterator:
            if result:
                main_course, vector_point = result
                main_course_objects.append(main_course)
                vector_data_points.append(vector_point)

    logger.info(f"Successfully transformed {len(main_course_objects)} out of {len(source_courses)} courses.")
    
    return main_course_objects, vector_data_points


def transform_programs_universal(source_programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    (This will be functional once program_processor.py is created)
    Orchestrates the parallel transformation of a list of source-clean programs.
    """
    logger.info(f"Starting universal transformation for {len(source_programs)} programs with {MAX_WORKERS} workers...")
    transformed_programs = []
    logger.info(f"Successfully transformed {len(transformed_programs)} out of {len(source_programs)} programs.")
    return transformed_programs