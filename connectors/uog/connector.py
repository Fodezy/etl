#!/usr/bin/env python3
# etl/connectors/uog/connector.py

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from core.connector_base import BaseConnector
from core.extractor import AsyncCoreExtractor
from connectors.uog.transformers.main import transform_courses_universal, transform_programs_universal

logger = logging.getLogger(__name__)

class UoGConnector(BaseConnector):
    name = "uog"

    def extract(self) -> str:
        """
        Kick off the async capture+parse run via asyncio.run(), then return
        the path to the raw JSON.
        """
        logger.info(f"UoGConnector.extract: calling AsyncCoreExtractor for '{self.name}'...")
        extractor = AsyncCoreExtractor(school_name=self.name)
        # run the async .run() method synchronously
        raw_data_path = asyncio.run(extractor.run())
        logger.info(f"UoGConnector.extract: AsyncCoreExtractor finished. Raw data at: {raw_data_path}")
        return raw_data_path

    def transform(self, raw_data_path: str) -> dict:
        """
        Map raw data from the filesystem into universal schemas.
        """
        logger.info(f"UoGConnector.transform: Reading raw data from {raw_data_path}")
        
        source_path = Path(raw_data_path)
        all_courses: List[Dict[str, Any]] = []
        all_programs: List[Dict[str, Any]] = []

        for json_file in source_path.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Program files have 'requirements'; course files have 'full_title'
                if 'requirements' in data:
                    all_programs.append(data)
                elif 'full_title' in data:
                    all_courses.append(data)

        logger.info(f"Loaded {len(all_courses)} raw course files and {len(all_programs)} raw program files.")

        # Decide whether to slice for testing
        courses_to_process = all_courses  # or all_courses[:5] for a quick run
        
        if len(courses_to_process) < len(all_courses):
            logger.info(f"--- RUNNING IN TEST MODE: Processing only the first {len(courses_to_process)} courses. ---")
        
        # Transform courses & programs
        if courses_to_process:
            transformed_courses, vector_points = transform_courses_universal(courses_to_process)
        else:
            transformed_courses, vector_points = [], []
        
        transformed_programs = transform_programs_universal(all_programs)

        # Ensure the cleaned output directory exists
        out_dir = Path(__file__).parent / "cleaned"
        out_dir.mkdir(exist_ok=True)

        logger.info(f"Saving {len(transformed_courses)} transformed courses...")
        # (rest of your saving logic goes here: e.g. write JSON, CSV, etc.)

        return {
            'courses': transformed_courses,
            'vectors': vector_points,
            'programs': transformed_programs
        }

    def load(self, norm: dict) -> None:
        logger.info("UoGConnector.load: stub - skipping database load stage")
        pass
