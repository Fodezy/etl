# University of Guelph (UoG) Connector

This connector extracts, transforms, and loads course and program data from the University of Guelph website into a standardized format for the CourseMap ETL pipeline.

## Overview

The UoG connector follows a standard ETL (Extract, Transform, Load) pattern:

1. **Extract**: Scrapes course and program data from the University of Guelph website
2. **Transform**: Converts the raw data into a standardized universal schema
3. **Load**: Prepares the data for loading into the target database (currently stubbed)

## Directory Structure

```
connectors/uog/
├── README.md                         # This documentation
├── connector.py                      # Main connector implementation
├── __init__.py                       # Package initialization
├── raw/                              # Raw extracted data
│   ├── subjects_with_courses.json    # Raw course data
│   ├── programs_with_sections.json   # Raw program data
│   └── __init__.py
├── cleaned/                          # Transformed data in universal schema
│   ├── universal_courses_cleaned.json
│   └── universal_programs_cleaned.json
├── extract/                          # Web scraping components
│   ├── README.md                     # Extract module documentation
│   ├── driver.py                     # Orchestrates all scraping stages
│   ├── course_catalog.py             # Stage 1: Scrape subjects
│   ├── subjects_with_courses.py      # Stage 2: Scrape courses
│   ├── program_catalog.py            # Stage 3: Scrape program list
│   ├── programs_with_sections.py     # Stage 4: Scrape program details
│   ├── parsers/                      # Data cleaning parsers
│   ├── scrapper_modules/             # Reusable scraping modules
│   └── data/                         # Intermediate JSON outputs
├── transformers/                     # Data transformation components
│   ├── README.md                     # Transformer documentation
│   ├── __init__.py
│   ├── scripts/                      # Utility scripts
│   ├── src/                          # Core transformation logic
│   │   ├── parser/                   # Prerequisite parsing components
│   │   │   ├── grammars/             # Lark grammar definitions
│   │   │   └── ...                   # Parser implementation files
│   │   ├── parse.py                  # Main parsing entry point
│   │   └── parse_prerequisite.py     # CLI entry point
│   ├── testReqs/                     # Test data files
│   └── tests/                        # Unit tests
└── load
```

## How It Works

### 1. Extract Phase

The extract phase uses web scraping to collect data from the University of Guelph website. It's organized into four stages:

1. **Stage 1**: Scrape the list of subjects (course catalog)
2. **Stage 2**: For each subject, scrape its courses
3. **Stage 3**: Scrape the program listing page
4. **Stage 4**: For each program, scrape its calendar sections

The `extract/driver.py` script orchestrates these stages, running them in parallel where possible. The final outputs are stored in the `raw/` directory:

- `subjects_with_courses.json`: Contains all courses organized by subject
- `programs_with_sections.json`: Contains all programs with their calendar sections

For more details, see the [Extract README](extract/README.md).

### 2. Transform Phase

The transform phase converts the raw data into a standardized universal schema. It uses specialized parsers to handle complex data like course prerequisites:

1. **Course Transformation**: Maps raw course data to the universal course schema
2. **Program Transformation**: Maps raw program data to the universal program schema
3. **Prerequisite Parsing**: Parses complex prerequisite statements into structured data

The transformed data is stored in the `cleaned/` directory:

- `universal_courses_cleaned.json`: Courses in the universal schema
- `universal_programs_cleaned.json`: Programs in the universal schema

For more details on the prerequisite parser, see the [Transformers README](transformers/README.md).

### 3. Load Phase

The load phase is currently stubbed in the connector implementation. It will eventually handle loading the transformed data into the target database.

## Usage

The connector is designed to be used through the main ETL pipeline. The `UoGConnector` class in `connector.py` implements the `BaseConnector` interface with the following methods:

- `extract()`: Runs the scraper driver and loads the raw JSON outputs
- `transform(raw)`: Maps raw data into universal course & program schemas
- `load(norm)`: Stubbed method for future database loading

## Requirements

- Python 3.8+
- `playwright` package for web scraping
- `lark-parser` package for prerequisite parsing

## Development

To extend or modify the connector:

1. **Extract**: Update the scraper modules in `extract/` to handle changes in the UoG website structure
2. **Transform**: Modify the transformation logic to map new fields or handle edge cases
3. **Load**: Implement the load method when the database integration is ready

## Testing

- Extract: Manual verification of scraped data
- Transform: Unit tests in `transformers/tests/`
- Integration: End-to-end testing through the main ETL pipeline