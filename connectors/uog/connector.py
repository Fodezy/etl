#!/usr/bin/env python3
# connectors/uog/connector.py

import json
import logging
from pathlib import Path

from core.connector_base import BaseConnector

# Loader is not yet implemented; load() is stubbed
# from core.loader import Loader

# scraper driver orchestration
from connectors.uog.extract.driver import main as run_scrapers
# transformation functions

# from connectors.uog.transformers.course_transformer import transform as transform_subjects_with_courses
# from connectors.uog.transformers.program_transformer import transform_programs_with_sections


logger = logging.getLogger(__name__)

class UoGConnector(BaseConnector):
    """
    Connector for University of Guelph data.
    Executes the scraping driver, then transforms data into universal schemas.
    """
    name = "uog"

    def extract(self) -> dict:
        """
        Run the scraper driver and load cleaned JSON outputs.
        Returns a dict with 'subjects_with_courses' and 'programs_with_sections'.
        """
        logger.info("UoGConnector.extract: running scrapers...")
        run_scrapers()

        raw_dir = Path(__file__).resolve().parent / 'raw'
        subs_file = raw_dir / 'subjects_with_courses.json'
        progs_file = raw_dir / 'programs_with_sections.json'

        missing = []
        if not subs_file.exists(): missing.append(str(subs_file))
        if not progs_file.exists(): missing.append(str(progs_file))
        if missing:
            msg = f"UoGConnector.extract: missing files: {', '.join(missing)}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        logger.info("UoGConnector.extract: loading raw JSON files")
        subjects_raw = json.loads(subs_file.read_text(encoding='utf-8'))
        programs_raw = json.loads(progs_file.read_text(encoding='utf-8'))

        return {
            'subjects_with_courses': subjects_raw,
            'programs_with_sections': programs_raw
        }

    def transform(self, raw: dict) -> dict:
        """
        Map raw data into universal course & program schemas.
        Returns normalized dict with 'courses' and 'programs'.
        """
        logger.info("UoGConnector.transform: transforming raw payloads")

        # use the aliased `transform_subjects_with_courses`
        courses_norm = [] #transform_subjects_with_courses(raw['subjects_with_courses'])
        programs_norm = []  # placeholder until you wire up program_transformer

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
