#!/usr/bin/env python3
# course_catalog.py

import json
from pathlib import Path
from .scrapper_modules.scrape_subjects_list import load_subjects, parse_subjects

def main():
    # 1. Scrape raw subjects from the UofG Courses page
    print("Stage 1: Loading raw subjects...")
    raw_subjects = load_subjects()

    # 2. Parse & normalize into text, name, specialization, code
    print("Stage 1: Parsing subjects...")
    subjects = parse_subjects(raw_subjects)

    # 3. Write to data/course_catalog/course_catalog.json
    output_dir  = Path("connectors/uog/extract/data/course_catalog")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "course_catalog.json"

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(subjects, f, ensure_ascii=False, indent=2)

    print(f"Stage 1: Saved {len(subjects)} subjects to {output_file}")

if __name__ == "__main__":
    main()
