#!/usr/bin/env python3
# driver.py
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Stage runners

def run_course_catalog():
    logger.info("→ Stage 1: course_catalog")
    from .course_catalog import main as stage1_main
    stage1_main()
    logger.info("✓ Stage 1 complete")


def run_program_catalog():
    logger.info("→ Stage 3: program_catalog")
    from .program_catalog import main as stage3_main
    stage3_main()
    logger.info("✓ Stage 3 complete")


def run_subjects_with_courses():
    logger.info("→ Stage 2: subjects_with_courses")
    from .subjects_with_courses import main as stage2_main
    asyncio.run(stage2_main())
    logger.info("✓ Stage 2 complete")


def run_programs_with_sections():
    logger.info("→ Stage 4: programs_with_sections")
    from .programs_with_sections import main as stage4_main
    asyncio.run(stage4_main())
    logger.info("✓ Stage 4 complete")


def main():
    # Run Stage 1 & 3 in parallel
    logger.info("Starting Stages 1 & 3 in parallel...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(run_course_catalog),
            executor.submit(run_program_catalog)
        ]
        for f in futures:
            f.result()

    # Run Stage 2 & 4 in parallel
    logger.info("Starting Stages 2 & 4 in parallel...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(run_subjects_with_courses),
            executor.submit(run_programs_with_sections)
        ]
        for f in futures:
            f.result()

    logger.info("Pipeline complete.")

if __name__ == '__main__':
    main()
