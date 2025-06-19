# CourseMap ETL Pipeline Plan: Transformer Stage
*Last Updated: June 19, 2025*

Fine-tined model: "fine_tuned_model": "ft:gpt-3.5-turbo-0125:fodey::BkGY16gt" 

COSTS ROUGHLY:

Training: 27.13 
single call: 0.00886
1600 calls: 14.18


without fine tune it would cost around: 145 per 1600 calls 


## Table of Contents

1.  [Overall Architecture](#overall-architecture)
2.  [Directory Structure](#directory-structure)
3.  [Transformer Orchestration (`main.py`)](#transformer-orchestration-mainpy)
4.  [Stream 1: Course Data Transformation](#stream-1-course-data-transformation)
5.  [Stream 2: Program Data Transformation](#stream-2-program-data-transformation)
6.  [Shared Enhancements](#shared-enhancements)
7.  [Action Items](#action-items)

---

## Overall Architecture

This document details **Phase 2** of a two-phase ETL process. The overall data flow is designed to be modular and robust.

* **Phase 1: Extraction & Parsing (`extract/` directory)**
    * **Responsibility:** Scrapes raw data from source websites (e.g., University of Guelph).
    * **Process:** Uses scripts in `extract/parsers/` to perform initial cleaning, converting messy web content into a predictable, structured JSON format.
    * **Output:** A set of "source-clean" JSON files. The data is clean and structured but still specific to the source's schema.

* **Phase 2: Transformation (`transformer/` directory)**
    * **Responsibility:** Ingests the "source-clean" JSON files from Phase 1.
    * **Process:** Maps the source-specific data to a final **universal schema** that is consistent across all potential data sources. This involves complex parsing, validation, and data enrichment.
    * **Output:** A final set of JSON objects conforming to the universal schema, ready for the `load` stage.

---

## Directory Structure

```
transformer/
├─ main.py
├─ program_transformer/
│  ├─ program_processor.py
│  └─ program_helper_parsers/
│     ├─ section_parser.py
│     ├─ department_parser.py
│     ├─ offering_pattern_parser.py
│     ├─ program_panels_parser.py
│     └─ requirement_group_parser.py
├─ course_transformer/
│  ├─ course_processor.py
│  ├─ course_helper_parsers/
│  │  └─ requisite_parser.py
│  └─ prompt-gen3.txt
├─ logs/
│  ├─ processed_courses.log
│  └─ failed_courses.log
└─ tests/
   ├─ transformer/
   │  ├─ test_course_processor.py
   │  ├─ test_requisite_parser.py
   │  ├─ test_program_processor.py
   │  └─ test_requirement_group_parser.py
   └─ end_to_end/
      └─ test_full_pipeline.py
```
---

## Transformer Orchestration (`main.py`)

**Responsibility:**
Provides top-level functions to orchestrate the transformation of course and program data streams. These functions are designed to be imported and called by an upstream ETL connector (e.g., `UoGConnector`).

**Key Functions:**

* `transform_courses_universal(source_courses: list) -> list`
    * Manages the transformation of the entire course data stream.
    * Uses a `concurrent.futures.ThreadPoolExecutor` to process individual courses in parallel, ideal for handling I/O-bound tasks like API calls in the helper parsers.
    * Delegates the transformation of each course to `course_processor.py`.

* `transform_programs_universal(source_programs: list) -> list`
    * Manages the transformation of the program data stream, following the same parallel processing pattern as the course transformer.
    * Delegates the transformation of each program to `program_processor.py`.

---

## Stream 1: Course Data Transformation

### `course_processor.py`

**Responsibility:**
Acts as the main "worker" for transforming a single course object.

**Process:**
1.  Receives a single "source-clean" course dictionary.
2.  Routes logical groups of data (`courseCode`, `prerequisites`, etc.) to dedicated helper parser functions.
3.  Assembles the returned, transformed data fragments.
4.  Validates the final, assembled object against the `universal-course.draft-09.json` schema.
5.  Returns a single, unified `Course` dictionary.

### `course_helper_parsers/`

#### `requisite_parser.py`

**Responsibilities:**
- Takes a raw prerequisite string as input (e.g., "One of CIS*1300, CIS*1500. A minimum grade of 70% is required.").
- Strips boilerplate wording and applies fast-path regex for simple patterns.
- For complex patterns, constructs a prompt from `prompt-gen3.txt` for an external API call (e.g., OpenAI).
- Its I/O-bound nature (waiting for the API) makes it a perfect candidate for the parallel execution managed by `main.py`.
- Logs failures and successes for monitoring and potential retries.
- Skips already-processed requisites by checking a cache or log file.
- Outputs a structured `RequisiteExpression` object according to the universal schema.

---

## Stream 2: Program Data Transformation

### `program_processor.py`

**Responsibility:**
Acts as the main "worker" for transforming a single program object.

**Process:**
1.  Receives a single "source-clean" program dictionary.
2.  Extracts and maps top-level fields (`code`, `name`, `degreeType`).
3.  Delegates complex sections (`panels`, `requirementGroups`) to specialized helper parsers.
4.  Validates the final object against the `universal-program.draft-02.json` schema.
5.  Returns a single, unified `Program` dictionary.

### `program_helper_parsers/`

#### `section_parser.py`

**Responsibilities:**
- Parses and normalizes various content sections (e.g., "Overview") into structured `Section` objects.

#### `requirement_group_parser.py`

**Responsibilities:**
- Parses each requirement "bucket" (e.g., "10.00 credits from List A") into a `RequirementGroup` object.
- Extracts course code references using regex, dedupes them, and builds structured `CourseRef` items.

---

## Shared Enhancements

-   **Schema Validation:** Use `jsonschema.validate()` on all final outputs from the `_processor` modules to ensure data integrity.
-   **Logging:** Employ hierarchical, structured logging (e.g., `loguru`) to provide context for each parser and transformation stream.
-   **Retry Strategy:** For any network or API calls (like in `requisite_parser.py`), use a library like `tenacity` with exponential backoff.
-   **Testing:**
    -   Unit tests for each helper parser with representative input/output fixtures.
    -   End-to-end tests that simulate the full `extract -> transform -> validate` pipeline.
-   **Caching:** Store results of expensive operations (like API calls) by a unique identifier (`courseCode`) to avoid redundant work on subsequent runs.

---

## Action Items

| Task                                                               | Priority | Owner                     |
| ------------------------------------------------------------------ | -------- | ------------------------- |
| Add schema validation calls in each `_processor` module            | High     | ETL Core                  |
| Implement `ThreadPoolExecutor` in `main.py` for parallel processing| High     | Orchestration             |
| Implement fast-path trivial prereq parsing                         | Medium   | `requisite_parser.py`     |
| Write end-to-end pipeline test                                     | High     | QA                        |
| Implement API result caching by `courseCode`                       | Medium   | `requisite_parser.py`     |