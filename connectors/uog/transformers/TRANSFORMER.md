# CourseMap ETL Pipeline Plan: Transformer Stage

_Last Updated: June 23, 2025_

## Project Status & Key Metrics

- **Fine-Tuned Model ID (Prerequisites):** `ft:gpt-3.5-turbo-0125:fodey::BkGY16gt`
- **Fine-Tuning Cost (One-Time):** ~$27.00 (for 1600 examples with a ~635 token prompt over 3 epochs).
- **Secondary Model (Program Restrictions):** Gemini Flash
  - Should be less than ~$0.10 per 1600 calls --> will be lower with caching
- **Local Models (Description Analysis):** `sentence-transformers/all-MiniLM-L6-v2` & `KeyBERT`
  - One-time model download, no per-call cost.
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
  - **Process:** Maps the source-specific data to final, universal schemas. This involves a hybrid approach of using fine-tuned models, general AI models, local ML models, and rule-based parsers for data enrichment.
  - **Output:** Two distinct sets of JSON objects: (1) a list of universal course objects and (2) a list of vector data points, ready for their respective loaders.

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
│     ├─ program_restriction_parser.py
│     ├─ section_parser.py
│     └─ description_parser.py
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

- `transform_courses_universal(source_courses: list) -> Tuple[list, list]`
  - Manages the transformation of the entire course data stream.
  - **Initializes a singleton instance of the `DescriptionParser`**, loading the local ML models into memory only once for efficiency.
  - Uses a `concurrent.futures.ThreadPoolExecutor` to process individual courses in parallel.
  - Delegates the transformation of each course to the `process_single_course` function, passing the course data and the initialized parser instance.
  - **Collects and separates the two types of results** (main course objects and vector points) into two distinct lists before returning them as a tuple.

---

## Stream 1: Course Data Transformation

### `course_processor.py`

**Responsibility:**
Acts as the main "worker" for transforming a single source course object into two distinct, final objects: a universal course object and a vector data point.

**Process:**

1.  Receives a single "source-clean" course dictionary and an initialized `DescriptionParser` instance.
2.  Orchestrates calls to a series of specialized helper parsers for each logical group of data.
3.  **Calls the `description_parser`** to clean the raw description text, generate a vector embedding, and extract keywords.
4.  Implements the "strip-and-pass" logic for the `restrictions` field.
5.  Intelligently combines structured prerequisite data from multiple fields.
6.  Assembles two distinct objects:
    - The main, unified `Course` dictionary, now including the extracted keywords as tags.
    - A `VectorPoint` dictionary containing the course ID and its generated vector embedding.
7.  Returns a tuple containing these two objects.

### `course_helper_parsers/`

#### `requisite_parser.py`
**Responsibilities:**
- Takes the raw `requisites` string as input.
- Calls the fine-tuned OpenAI model (`ft:gpt-3.5-turbo...`) to parse the string into a structured `RequisiteExpression` object.

#### `department_parser.py`
**Responsibilities:**
- Parses a department name string into a structured `Department` object.
- Uses comprehensive, pre-populated lookup maps to find the department's official short code and its parent college.

#### `antirequisite_parser.py`
**Responsibilities:**
- Scans the `restrictions` string for specific trigger phrases (e.g., "credit will not be given for").
- Extracts only true antirequisite course codes using regular expressions.

#### `terms_offered_parser.py`
**Responsibilities:**
- Parses the `offered` string (e.g., "Winter Only, All Years") into a structured `OfferingPattern` object.

#### `program_restriction_parser.py`
**Responsibilities:**
- Takes a filtered `restrictions` string as input (after antirequisites have been stripped out).
- Calls the Gemini Flash API to find and structure rules like program enrollment or instructor consent.

#### `section_parser.py`
**Responsibilities:**
- Parses a list of raw section data, extracting details for meeting times, instructors, seat capacity, and delivery mode.

#### `description_parser.py`
**Responsibilities:**
- **Data Cleaning:** Takes a raw description string and isolates the core descriptive text by finding and removing administrative sections (e.g., "Offering(s):", "Restriction(s):") using regular expressions.
- **Vectorization:** Uses the `sentence-transformers` library (`all-MiniLM-L6-v2`) to convert the *cleaned* description into a 384-dimension vector embedding for semantic search.
- **Keyword Extraction:** Uses the `KeyBERT` library to extract relevant keywords and phrases from the *cleaned* description to be used as filterable tags.
- **Efficiency:** Implemented as a class to ensure the heavy ML models are loaded into memory only once per ETL run.

---

## Testing Strategy (`test_transformer.py`)

**Responsibility:**
Provides a self-contained script for running a small-scale, end-to-end test of the transformation pipeline.

**Process:**

1.  Loads a subset of the full `subjects_with_courses.json` source data.
2.  Simulates expensive API calls by using "golden datasets":
    - Loads pre-parsed prerequisites from `Golden_DataSet_Final.jsonl` into a lookup map to simulate the OpenAI model.
    - Uses a hardcoded dictionary to simulate the output of the Gemini-based `program_restriction_parser`.
3.  **Performs a real, end-to-end test of the description processing pipeline** by initializing and using the actual `DescriptionParser` to generate real vectors and tags for the test data subset.
4.  Calls the `process_single_course` worker for each course, passing the real `DescriptionParser` instance and the simulated data for other parsers.
5.  **Saves the final transformed outputs to two separate files** for review and validation: `test_output_universal_courses.json` and `test_output_universal_vectors.json`.

---

## Stream 2: Program Data Transformation

_(This stream is not yet implemented)_

---

## Shared Enhancements

_(This section remains a list of future goals)_

---

## Action Items

| Task                                                     | Status    | Owner                                                   |
| :------------------------------------------------------- | :-------- | :------------------------------------------------------ |
| Implement `ThreadPoolExecutor` in `main.py`                | **Done** | Orchestration                                           |
| Implement `requisite_parser` with fine-tuned model       | **Done** | `requisite_parser.py`                                   |
| Implement `department_parser` with lookup maps           | **Done** | `department_parser.py`                                  |
| Implement `antirequisite_parser` with keyword logic      | **Done** | `antirequisite_parser.py`                                 |
| Implement `terms_offered_parser` helper                  | **Done** | `terms_offered_parser.py`                                 |
| Implement `program_restriction_parser` with Gemini       | **Done** | `program_restriction_parser.py`                           |
| Implement `section_parser` helper                       | **Done** | `section_parser.py`                                     |
| Implement `description_parser` with cleaning & ML models | **Done** | `description_parser.py`                                 |
| Add schema validation calls in each `_processor` module    | **To-Do** | ETL Core                                                |
| Implement API result caching                             | **To-Do** | `requisite_parser.py` / `program_restriction_parser.py` |