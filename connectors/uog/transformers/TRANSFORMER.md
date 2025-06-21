# CourseMap ETL Pipeline Plan: Transformer Stage

_Last Updated: June 20, 2025_

## Project Status & Key Metrics

- **Fine-Tuned Model ID:** `ft:gpt-3.5-turbo-0125:fodey::BkGY16gt` [cite: { "object": "fine_tuning.job", ... }]
- **Fine-Tuning Cost (One-Time):** ~$27.00 (for 1600 examples with a ~635 token prompt over 3 epochs).
- **Secondary Model:** Gemini 2.0 Flash (for parsing program restrictions).
  - should be less then ~$0.10 per 1600 calls --> will be lower with caching
- **Inference Cost (Fine-Tuned Model):**
  - **Per Call (Avg):** ~$0.00886
  - **Per 1600 Courses:** ~$14.18
- **Cost Savings vs. Base `gpt-4o`:** ~90% reduction in operational cost for course prerequisite parsing.

## Table of Contents

1.  [Overall Architecture](#overall-architecture)
2.  [Directory Structure](#directory-structure)
3.  [Transformer Orchestration (`main.py`)](#transformer-orchestration-mainpy)
4.  [Stream 1: Course Data Transformation](#stream-1-course-data-transformation)
5.  [Testing Strategy (`test_transformer.py`)](#testing-strategy-test_transformerpy)
6.  [Stream 2: Program Data Transformation](#stream-2-program-data-transformation)
7.  [Shared Enhancements](#shared-enhancements)
8.  [Action Items](#action-items)

---

## Overall Architecture

This document details **Phase 2** of a two-phase ETL process. The overall data flow is designed to be modular and robust.

- **Phase 1: Extraction & Parsing (`extract/` directory)**

  - **Responsibility:** Scrapes raw data from source websites.
  - **Process:** Uses scripts in `extract/parsers/` to perform initial cleaning, converting messy web content into a predictable, structured JSON format.
  - **Output:** A set of "source-clean" JSON files. The data is clean and structured but still specific to the source's schema.

- **Phase 2: Transformation (`transformer/` directory)**
  - **Responsibility:** Ingests the "source-clean" JSON files from Phase 1.
  - **Process:** Maps the source-specific data to a final **universal schema**. This involves a hybrid approach of using fine-tuned models, general AI models, and rule-based parsers for data enrichment.
  - **Output:** A final set of JSON objects conforming to the universal schema, ready for the `load` stage.

---

## Directory Structure

```
transformer/
├─ main.py
├─ program_transformer/
│  ├─ program_processor.py (Stub)
│  └─ program_helper_parsers/
├─ course_transformer/
│  ├─ course_processor.py
│  └─ course_helper_parsers/
│     ├─ requisite_parser.py
│     ├─ department_parser.py
│     ├─ antirequisite_parser.py
│     ├─ terms_offered_parser.py
│     └─ program_restriction_parser.py
├─ logs/
│  ├─ processed.log
│  └─ failed.log
└─ tests/
   └─ test_transformer.py
```

---

## Transformer Orchestration (`main.py`)

**Responsibility:**
Provides top-level functions that orchestrate the transformation of course and program data streams. These functions are designed to be imported and called by an upstream ETL connector.

**Key Functions:**

- `transform_courses_universal(source_courses: list) -> list`
  - Manages the transformation of the entire course data stream.
  - Uses a `concurrent.futures.ThreadPoolExecutor` to process individual courses in parallel, ideal for handling I/O-bound tasks like API calls.
  - Delegates the transformation of each course to the `process_single_course` function.

---

## Stream 1: Course Data Transformation

### `course_processor.py`

**Responsibility:**
Acts as the main "worker" for transforming a single source course object into the universal schema

**Process:**

1.  Receives a single "source-clean" course dictionary.
2.  Orchestrates calls to a series of specialized helper parsers for each logical group of data.
3.  Implements the "strip-and-pass" logic for the `restrictions` field: it first calls the `antirequisite_parser`, removes the found antirequisites from the string, and then passes the filtered string to the `program_restriction_parser`
4.  Intelligently combines the structured prerequisite data from both the `requisites` and `restrictions` fields into a single, comprehensive `prerequisites` object
5.  Assembles all transformed data fragments into a single, unified `Course` dictionary.

### `course_helper_parsers/`

#### `requisite_parser.py`

**Responsibilities:**

- Takes the raw `requisites` string as input.
- Calls the fine-tuned OpenAI model (`ft:gpt-3.5-turbo...`) to parse the string into a structured `RequisiteExpression` object

#### `department_parser.py`

**Responsibilities:**

- Parses a department name string into a structured `Department` object.
- Uses comprehensive, pre-populated lookup maps to find the department's official short code and its parent college

#### `antirequisite_parser.py`

**Responsibilities:**

- Scans the `restrictions` string for specific trigger phrases (e.g., "credit will not be given for") or patterns (e.g., starting with a course code).
- Extracts only true antirequisite course codes using regular expressions, ignoring other text.

#### `terms_offered_parser.py`

**Responsibilities:**

- Parses the `offered` string (e.g., "Winter Only, All Years") into a structured `OfferingPattern` object with `terms`, `years`, and `note` fields.

#### `program_restriction_parser.py`

**Responsibilities:**

- Takes a filtered `restrictions` string as input (after antirequisites have been stripped out).
- Calls the Gemini Flash API with a specialized prompt to find and structure rules like program enrollment or instructor consent.

---

## Testing Strategy (`test_transformer.py`)

**Responsibility:**
Provides a self-contained script for running an end-to-end test of the transformation pipeline **without** making live API calls.

**Process:**

1.  Loads the full `subjects_with_courses.json` source data
2.  Loads a "golden dataset" of pre-parsed prerequisites from `Golden_DataSet_Final.jsonl` into a lookup map to simulate the OpenAI fine-tuned model's output
3.  Simulates the `program_restriction_parser` by using a small, hardcoded dictionary of expected outputs for common restriction strings
4.  Calls the `process_single_course` worker for each course, which uses the real helper parsers but injects the "golden" data instead of making API calls.
5.  Saves the final transformed output to `test_output_universal_courses.json` for review and validation.

---

## Stream 2: Program Data Transformation

_(This stream is not yet implemented)_

---

## Shared Enhancements

_(This section remains a list of future goals)_

---

## Action Items

| Task                                                     | Status    | Owner                                                   |
| -------------------------------------------------------- | --------- | ------------------------------------------------------- |
| Implement `ThreadPoolExecutor` in `main.py`              | **Done**  | Orchestration                                           |
| Implement `requisite_parser` with fine-tuned model       | **Done**  | `requisite_parser.py`                                   |
| Implement `department_parser` with lookup maps           | **Done**  | `department_parser.py`                                  |
| Implement `antirequisite_parser` with keyword logic      | **Done**  | `antirequisite_parser.py`                               |
| Implement `terms_offered_parser` helper                  | **Done**  | `terms_offered_parser.py`                               |
| Implement `program_restriction_parser` with Gemini       | **Done**  | `program_restriction_parser.py`                         |
| Implement `_parse_sections` helper (and its sub-parsers) | **To-Do** | `course_processor.py`                                   |
| Add schema validation calls in each `_processor` module  | **To-Do** | ETL Core                                                |
| Implement API result caching                             | **To-Do** | `requisite_parser.py` / `program_restriction_parser.py` |
