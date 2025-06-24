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
        clean_data_path = asyncio.run(extractor.run())
        logger.info(f"UoGConnector.extract: AsyncCoreExtractor finished. Raw data at: {clean_data_path}")
        return clean_data_path

    def transform(self, clean_data_path: str) -> dict:
        """
        Map cleaned data from the filesystem into universal schemas.
        """
        logger.info(f"UoGConnector.transform: Reading cleaned data from {clean_data_path}")
        
        source_path = Path(clean_data_path)
        if not source_path.exists():
            logger.error(f"Connector: Cannot run Transform. Data path not found: {source_path}")
            raise FileNotFoundError(f"Data path not found: {source_path}")

        all_courses: List[Dict[str, Any]] = []
        all_programs: List[Dict[str, Any]] = []

        for json_file in source_path.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if 'requirements' in data:
                    all_programs.append(data)
                elif 'code' in data:
                    all_courses.append(data)

        logger.info(f"Loaded {len(all_courses)} course files and {len(all_programs)} program files.")

        # --- FOR A FULL RUN, UNCOMMENT THE FIRST LINE AND COMMENT THE SECOND ---
        # courses_to_process = all_courses
        courses_to_process = all_courses[:5]
        
        if len(courses_to_process) < len(all_courses):
            logger.warning(f"--- RUNNING IN TEST MODE: Processing only the first {len(courses_to_process)} courses. ---")
        
        transformed_courses, vector_points = transform_courses_universal(courses_to_process) if courses_to_process else ([], [])
        transformed_programs = transform_programs_universal(all_programs)

        return {
            'courses': transformed_courses,
            'vectors': vector_points,
            'programs': transformed_programs
        }

    # --- UPDATED LOAD METHOD ---
    def load(self, norm: dict) -> None:
        """
        Saves the transformed, normalized data to a final JSON output file.
        """
        logger.info(f"UoGConnector.load: Saving {len(norm.get('courses', []))} courses to file...")
        
        # Define the output directory relative to this connector file
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define the output file path
        output_file_path = output_dir / "universal_courses_cleaned.json"

        # Write the 'courses' list to the JSON file
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                # We are saving just the courses list for this example
                json.dump(norm.get('courses', []), f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved cleaned data to {output_file_path}")
        except Exception as e:
            logger.error(f"Failed to save data to {output_file_path}: {e}")