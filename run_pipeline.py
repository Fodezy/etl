#!/usr/bin/env python3
"""
ETL orchestrator for all university connectors.
Extract → Clean → Transform → Load
"""
import logging
import argparse
import importlib
import pkgutil
from pathlib import Path

# Load .env first
from dotenv import load_dotenv
load_dotenv()

from core.connector_base import BaseConnector
import core.cleaner  as cleaner# <-- our universal cleaner

# --- setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def discover_connectors():
    """Dynamically find all connectors in connectors/"""
    for _, mod_name, _ in pkgutil.iter_modules(['connectors']):
        mod = importlib.import_module(f"connectors.{mod_name}.connector")
        for obj in vars(mod).values():
            if isinstance(obj, type) \
               and issubclass(obj, BaseConnector) \
               and obj is not BaseConnector:
                yield obj()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run ETL pipelines for university connectors.")
    p.add_argument(
        '--connectors',
        nargs='*',
        help='Which specific connectors to run (e.g., uog). Runs all if not specified.'
    )
    p.add_argument(
        '--phases',
        type=str,
        default='ETL',
        help='A string of phases to run (E=Extract+Clean, T=Transform, L=Load).'
    )
    args = p.parse_args()
    phases_to_run = set(args.phases.upper())

    for conn in discover_connectors():
        if args.connectors and conn.name not in args.connectors:
            continue

        logger.info(f"--- Starting connector: {conn.name} for phases: {args.phases} ---")
        raw_data_path = str(Path("connectors") / conn.name / "extract" / "clean")
        norm_data = {}

        # --- EXTRACT + CLEAN ---
        if 'E' in phases_to_run:
            logger.info("--- Running EXTRACT stage ---")
            # extract() returns path to raw/<school_id>
            raw_data_path = conn.extract()
            # now clean it in-place into connectors/<school_id>/clean
            logger.info("--- Running CLEAN stage ---")
            cleaner.clean_school(conn.name)
            # point downstream at the cleaned folder
            raw_data_path = str(Path("connectors") / conn.name / "extract" / "clean")
            logger.info(f"Cleaned data available at: {raw_data_path}")

        # --- TRANSFORM ---
        if 'T' in phases_to_run:
            if not raw_data_path or not Path(raw_data_path).exists():
                logger.error(f"T-Phase: Cannot run Transform. Data path not found: {raw_data_path}.")
                continue
            logger.info("--- Running TRANSFORM stage ---")
            norm_data = conn.transform(raw_data_path)

        # --- LOAD ---
        if 'L' in phases_to_run:
            if not norm_data:
                logger.error("Cannot run Load. Normalized data not available.")
                continue
            logger.info("--- Running LOAD stage ---")
            conn.load(norm_data)

        logger.info(f"--- Finished connector: {conn.name} ---")
