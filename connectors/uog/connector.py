#!/usr/bin/env python3
# connectors/uog/connector.py

import json
import logging
from pathlib import Path

from core.connector_base import BaseConnector
from connectors.uog.extract.driver import main as run_scrapers
from connectors.uog.extract.parsers.subjects_with_courses_parser import parse_subjects_with_courses
from connectors.uog.extract.parsers.programs_with_sections_parser import parse_programs_with_sections
# ... (other imports) ...

logger = logging.getLogger(__name__)

class UoGConnector(BaseConnector):
    # ... (name property) ...
    name = "uog"

    def extract(self) -> dict:
        """
        Run the scraper driver and get the cleaned data directly.
        Returns a dict with 'subjects_with_courses' and 'programs_with_sections'.
        """
        logger.info("UoGConnector.extract: running scrapers...")
        # Capture the dictionary returned by the driver
        scraped_data = run_scrapers()

        # The driver now provides the data directly, so we no longer need to read files here.
        # We can simply return the data we received.
        logger.info("UoGConnector.extract: received data directly from driver.")

        # Basic validation to ensure the keys are present
        if 'subjects_with_courses' not in scraped_data or 'programs_with_sections' not in scraped_data:
            msg = "UoGConnector.extract: driver did not return the expected data keys."
            logger.error(msg)
            raise KeyError(msg)

        return scraped_data

    def transform(self, raw: dict) -> dict:
        """
        Map raw data into universal course & program schemas.
        Returns normalized dict with 'courses' and 'programs'.
        """
        logger.info("UoGConnector.transform: Unpacking raw data payloads...")

        # use the aliased `transform_subjects_with_courses`
        courses_norm = raw['subjects_with_courses'] # --> change this for now to read in the raw json file
        logger.info(f"Successfully unpacked the 'subjects_with_courses' payload.")

        programs_norm = raw['programs_with_sections'] # --> change this for now to read in the raw json file
        logger.info(f"Successfully unpacked the 'programs_with_sections' payload.")

        # CALL THE TRANSFORMER SECTION HERE BELLOW 




        out_dir = Path(__file__).parent / "cleaned"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "universal_courses_cleaned.json").write_text(
            json.dumps(courses_norm, indent=2), encoding='utf-8'
        )
        (out_dir / "universal_programs_cleaned.json").write_text(
            json.dumps(programs_norm, indent=2), encoding='utf-8'
        )

        return {
            'courses': courses_norm,
            'programs': programs_norm
        }

    def load(self, norm: dict) -> None:
        """
        Stubbed load: loader integration will be added once ready.
        """


        logger.info("UoGConnector.load: stub - skipping database load stage")