#!/usr/bin/env python3
# program_catalog.py

import asyncio
import json
import logging
from pathlib import Path

from .scrapper_modules.scrape_program_list import scrape_program_list

# Configure logging to match other project files
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


async def extract_and_parse_program_catalog(write_json: bool = True) -> list:
    """
    Stage 3: Scrape the UofG program catalog list.
    Optionally writes JSON output and returns the parsed list of programs.

    Args:
        write_json (bool): If True, write the catalog JSON to disk.

    Returns:
        list: A list of dictionaries, where each dict is a parsed program.
    """
    logger.info("Stage 3: Scraping program list...")
    programs = await scrape_program_list()
    logger.info(f"Stage 3: Retrieved {len(programs)} programs.")

    if write_json:
        base_dir = Path(__file__).resolve().parent
        output_dir = base_dir / "data" / "programs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "program_catalog.json"

        logger.info(f"Stage 3: Writing {len(programs)} programs to {output_file}")
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(programs, f, ensure_ascii=False, indent=2)

    return programs


if __name__ == '__main__':
    # This block allows the script to be run standalone for testing
    # It now calls the primary async function
    results = asyncio.run(extract_and_parse_program_catalog(write_json=True))
    if results:
        logger.info(f"✔ program_catalog.json contains {len(results)} entries.")