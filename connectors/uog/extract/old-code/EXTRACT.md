# CourseMap ETL Pipeline Plan: EXTRACT

This project automates scraping and processing of course and program data from the University of Guelph website. It is organized into four stages, each with its own script and output JSON. A central driver orchestrates these stages in parallel where possible.

---

## File Structure

```text
extract/
├── README.md                         # This documentation
├── driver.py                         # Orchestrates all four stages in phases
├── course_catalog.py            DONE # Stage 1: Scrape subjects → course_catalog.json
├── subjects_with_courses.py     DONE # Stage 2: Scrape courses → subjects_with_courses.json
├── program_catalog.py           DONE # Stage 3: Scrape program list → program_catalog.json
├── programs_with_sections.py    DONE # Stage 4: Scrape program calendar sections → programs_with_sections.json
├── parsers/
│   ├── subjects_with_courses_parser.py  # Clean & format raw course data
│   └── programs_with_sections_parser.py # Clean & format raw program sections JSON
├── scrapper_modules/                    # Reusable scraping modules
│   ├── scrape_subjects_list.py   DONE   # load_subjects(), parse_subjects(), load_courses()
│   ├── scrape_program_list.py    DONE   # scrape_program_list()
│   └── scrape_program_calendar.py DONE  # scrape_program() and async calendar logic
└── data/                                # JSON outputs organized by stage
    ├── course_catalog/
    │   ├── course_catalog.json    DONE  # Output of Stage 1
    │   ├── subjects_with_courses_raw.json  # Intermediate raw output of Stage 2
    │   └── subjects_with_courses.json      # Cleaned output of Stage 2
    └── programs/
        ├── program_catalog.json   DONE  # Output of Stage 3
        ├── programs_with_sections_raw.json # Intermediate raw output of Stage 4
        └── programs_with_sections.json     # Cleaned output of Stage 4
```

---

## Stage 1: course_catalog.py

**Purpose**: Scrape the list of subjects (course catalog) from the UofG Courses page, parse and normalize, then write `course_catalog.json`.

- **Input**: none
- **Output**: `course_catalog.json`

**Key functions**:
- `load_subjects()` from `scrapper_modules/scrape_subjects_list.py`
- `parse_subjects(raw_list)` to split name, specialization, and code

**Status**: COMPLETE ✓

---

## Stage 2: subjects_with_courses.py

**Purpose**: Read `course_catalog.json`, then for each subject code scrape its courses concurrently and write:

- **Intermediate**: `subjects_with_courses_raw.json`
- **Output**: `subjects_with_courses.json`

**Input**: `course_catalog.json`

**Key functions**:
- `load_courses(subject_name)` from `scrapper_modules/scrape_subjects_list.py`
- Thread pool to run up to 5 scrapers in parallel
- `subjects_with_courses_parser.py` to post-process and clean the raw output

**Status**: COMPLETE ✓

---

## Stage 3: program_catalog.py

**Purpose**: Scrape the UofG Programs listing page, collect program names, degrees, and calendar URLs, then write `program_catalog.json`.

- **Input**: none
- **Output**: `program_catalog.json`

**Key functions**:
- `scrape_program_list()` from `scrapper_modules/scrape_program_list.py`

**Status**: COMPLETE ✓

---

## Stage 4: programs_with_sections.py

**Purpose**: Read `program_catalog.json`, then for each program scrape its calendar sections (Overview, Major, Co‑op, etc.) asynchronously and write:

- **Intermediate**: `programs_with_sections_raw.json`
- **Output**: `programs_with_sections.json`

**Input**: `program_catalog.json`

**Key functions**:
- `scrape_program(program_meta)` from `scrapper_modules/scrape_program_calendar.py`
- `asyncio` + semaphore to limit concurrency
- `programs_with_sections_parser.py` to post-process and clean the raw output

**Status**: COMPLETE ✓

---

## Parsers

Before dumping final JSON in Stages 2 and 4, raw output is passed through a parser to:

- Normalize field names
- Remove empty entries
- Flatten nested arrays where appropriate
- Validate required keys are present

**Parser files** in `parsers/`:
- `subjects_with_courses_parser.py`: Cleans and normalizes course data
- `programs_with_sections_parser.py`: Processes program sections with specialized regex patterns

Each provides a function `parse_<stage>(raw_json)` that returns cleaned data.

---

## driver.py

This script orchestrates all four stages in two parallel phases:

1. **Phase A (catalogs)**:
   - Stage 1: `course_catalog.py`
   - Stage 3: `program_catalog.py`

2. **Phase B (details)**:
   - Stage 2: `subjects_with_courses.py`
   - Stage 4: `programs_with_sections.py`

**Usage**:
```bash
python driver.py
```

The driver ensures each stage's inputs are ready before running its dependents, while maximizing concurrency where safe.

---

## Data Flow

1. **Stage 1** scrapes subject listings → `course_catalog.json`
2. **Stage 3** scrapes program listings → `program_catalog.json`
3. **Stage 2** uses `course_catalog.json` to scrape detailed course info → `subjects_with_courses.json`
4. **Stage 4** uses `program_catalog.json` to scrape program details → `programs_with_sections.json`

Final outputs are stored in `connectors/uog/raw/` for downstream processing.

---

## Requirements

- Python 3.8+
- `playwright` package
- Internet access to UofG sites

Install dependencies:
```bash
pip install playwright
playwright install
```

---

## Customization

Feel free to adjust:
- ThreadPool sizes (`max_workers`)
- Async semaphore (`MAX_CONCURRENT`)
- Parser logic to handle edge cases in the HTML structure

---

## Implementation Status

All components of the ETL pipeline are now complete:

- ✓ Stage 1: Course catalog scraping
- ✓ Stage 2: Subject course details scraping
- ✓ Stage 3: Program catalog scraping
- ✓ Stage 4: Program sections scraping
- ✓ All parser modules
- ✓ Driver orchestration

The system is fully functional and can be run using the driver script.