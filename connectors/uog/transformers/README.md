
```
transformers/
├── src/
│    ├── __init__.py
│    ├── parse_prereq.py        # <--- The Main Public Entry Point
│    └── parser/
│        ├── __init__.py
│        └── requisite_parser/      # <--- The Core Parsing Engine
│            ├── __init__.py
│            ├── parser.py          # Orchestrates parsing with Lark
│            ├── transformer.py     # Converts the parse tree to JSON
│            └── grammars/          # Lark grammar files
│                ├── __init__.py
│                ├── requisite.lark # The main, unified grammar
│                └── common.lark    # Shared terminals (best practice)
└── test/
     ├── test_parser.py
```

# sprint 1:

# Prerequisite Parsing System

This directory contains the components for a robust system designed to parse university course prerequisite strings into a structured, logical format.

## System Architecture

The system is designed around a context-aware, recursive-descent parser using the Lark library. This approach avoids the pitfalls of simple string splitting and correctly handles the complex, nested logic inherent in prerequisite rules.

The main components are:

* **`parse_prereq.py`**: The simple, public-facing entry point for the system.

* **`parser/requisite_parser/`**: A self-contained directory that houses the core parsing engine.

  * `parser.py`: Orchestrates the parsing process.

  * `transformer.py`: Converts the raw parse tree into a clean JSON structure.

  * `grammars/`: Contains the `.lark` files that formally define the "language" of prerequisites.

## Development Plan

The system is being developed in a series of sprints, each focusing on a core piece of functionality and its corresponding unit tests.

* **Sprint 1: Project Scaffolding:** Set up the file structure and test environment.

* **Sprint 2 & Beyond:** Incrementally add parsing capabilities for different types of prerequisite rules (e.g., single courses, logical operators, "N of" lists).

# sprint 2:

# Prerequisite Parsing System

This directory contains the components for a robust system designed to parse university course prerequisite strings into a structured, logical format.

## System Architecture

The system is designed around a context-aware, recursive-descent parser using the Lark library. This approach avoids the pitfalls of simple string splitting and correctly handles the complex, nested logic inherent in prerequisite rules.

The main components are:

* **`parse_prereq.py`**: The simple, public-facing entry point for the system.
* **`parser/requisite_parser/`**: A self-contained directory that houses the core parsing engine.
  * `parser.py`: Orchestrates the parsing process.
  * `transformer.py`: Converts the raw parse tree into a clean JSON structure.
  * `grammars/`: Contains the `.lark` files that formally define the "language" of prerequisites.

## Development Plan

The system is being developed in a series of sprints, each focusing on a core piece of functionality and its corresponding unit tests.

* **Sprint 1: Project Scaffolding:** Set up the file structure and test environment.
* **Sprint 2: Single Course Parsing:** Implemented the ability to parse a single course code (e.g., `CIS*1910`) and clean trailing commentary.
* **Sprint 3 & Beyond:** Incrementally add parsing capabilities for logical operators, "N of" lists, and other requirement types.

## JSON Schema (In-Progress)

### Course
```json
{
  "type": "COURSE",
  "code": "CIS*2500"
}
```

# sprint 3:
# Prerequisite Parsing System

This directory contains the components for a robust system designed to parse university course prerequisite strings into a structured, logical format.

## System Architecture

The system is designed around a context-aware, recursive-descent parser using the Lark library. This approach avoids the pitfalls of simple string splitting and correctly handles the complex, nested logic inherent in prerequisite rules.

The main components are:

* **`parse_prereq.py`**: The simple, public-facing entry point for the system.
* **`parser/requisite_parser/`**: A self-contained directory that houses the core parsing engine.
  * `parser.py`: Orchestrates the parsing process.
  * `transformer.py`: Converts the raw parse tree into a clean JSON structure.
  * `grammars/`: Contains the `.lark` files that formally define the "language" of prerequisites.

## Development Plan

The system is being developed in a series of sprints, each focusing on a core piece of functionality and its corresponding unit tests.

* **Sprint 1: Project Scaffolding:** Set up the file structure and test environment.
* **Sprint 2: Single Course Parsing:** Implemented the ability to parse a single course code (e.g., `CIS*1910`) and clean trailing commentary.
* **Sprint 3: Logical Operators:** Implemented parsing for `AND` (comma) and `OR` expressions with correct operator precedence.
* **Sprint 4 & Beyond:** Incrementally add parsing capabilities for grouping, "N of" lists, and other requirement types.

## JSON Schema (In-Progress)

### Course
```json
{
  "type": "COURSE",
  "code": "CIS*2500"
}
```

# sprint 4: 
# Prerequisite Parsing System

This directory contains the components for a robust system designed to parse university course prerequisite strings into a structured, logical format.

## System Architecture

The system is designed around a context-aware, recursive-descent parser using the Lark library. This approach avoids the pitfalls of simple string splitting and correctly handles the complex, nested logic inherent in prerequisite rules.

The main components are:

* **`parse_prereq.py`**: The simple, public-facing entry point for the system.
* **`parser/requisite_parser/`**: A self-contained directory that houses the core parsing engine.
  * `parser.py`: Orchestrates the parsing process.
  * `transformer.py`: Converts the raw parse tree into a clean JSON structure.
  * `grammars/`: Contains the `.lark` files that formally define the "language" of prerequisites.

## Development Plan

The system is being developed in a series of sprints, each focusing on a core piece of functionality and its corresponding unit tests.

* **Sprint 1: Project Scaffolding:** Set up the file structure and test environment.
* **Sprint 2: Single Course Parsing:** Implemented the ability to parse a single course code and clean trailing commentary.
* **Sprint 3: Logical Operators:** Implemented parsing for `AND` (comma) and `OR` expressions with correct operator precedence.
* **Sprint 4: Grouping and Nesting:** Implemented parsing for nested expressions using `()` and `[]`.
* **Sprint 5 & Beyond:** Incrementally add parsing capabilities for "N of" lists and other requirement types.

## JSON Schema (In-Progress)

### Course
```json
{
  "type": "COURSE",
  "code": "CIS*2500"
}
```