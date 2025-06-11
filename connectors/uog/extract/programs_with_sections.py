#!/usr/bin/env python3
# programs_with_sections.py

import asyncio
import json
import logging
from pathlib import Path

from .scrapper_modules.scrape_program_calendar import scrape_program
from .parsers.programs_with_sections_parser import parse_programs_with_sections

# Concurrency setting (max number of parallel scrapes)
MAX_CONCURRENT = 5

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

async def main():
    # Load program catalog
    base_dir = Path(__file__).resolve().parent
    catalog_file = base_dir / 'data' / 'programs' / 'program_catalog.json'
    if not catalog_file.exists():
        logger.error(f"Program catalog not found at {catalog_file}")
        return

    logger.info(f"Stage 4: Loading program catalog from {catalog_file}")
    programs = json.loads(catalog_file.read_text(encoding='utf-8'))

    # Scrape sections concurrently
    logger.info(
        f"Stage 4: Scraping sections for {len(programs)} programs (max {MAX_CONCURRENT} concurrent)"
    )
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        tasks = [
            asyncio.create_task(scrape_program(prog, browser, semaphore))
            for prog in programs
        ]
        raw_results = await asyncio.gather(*tasks)
        await browser.close()

    # Write raw output (intermediate)
    raw_dir = base_dir / 'data' / 'programs'
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / 'programs_with_sections_raw.json'
    raw_file.write_text(
        json.dumps(raw_results, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    logger.info(f"Stage 4: Saved raw sections to {raw_file}")

    # Clean and normalize
    logger.info("Stage 4: Cleaning and normalizing program sections...")
    cleaned = parse_programs_with_sections(raw_results)

    # Write cleaned output to new raw location
    cleaned_dir = base_dir.parent / 'raw'
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    clean_file = cleaned_dir / 'programs_with_sections.json'
    clean_file.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    logger.info(f"Stage 4: Saved cleaned sections to {clean_file}")

if __name__ == '__main__':
    asyncio.run(main())
