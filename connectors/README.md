# CourseMap ETL Connectors

This directory contains data connectors for the CourseMap ETL (Extract, Transform, Load) pipeline. Each connector is responsible for extracting data from a specific university's course catalog, transforming it into a standardized format, and preparing it for loading into the CourseMap database.

## Overview

Connectors follow a standard ETL pattern:

1. **Extract**: Scrape or download raw data from university websites or APIs
2. **Transform**: Convert raw data into standardized universal schemas
3. **Load**: Prepare data for loading into the target database

Each connector is implemented as a Python package that follows a consistent interface, making it easy to add new data sources to the system.

## Directory Structure

```
connectors/
├── README.md                     # This documentation
├── __init__.py                   # Package initialization
├── uog/                          # University of Guelph connector
│   ├── README.md                 # UoG connector documentation
│   ├── __init__.py
│   ├── connector.py              # Main connector implementation
│   ├── raw/                      # Raw extracted data
│   ├── cleaned/                  # Transformed data in universal schema
│   ├── extract/                  # Web scraping components
│   ├── transformers/             # Data transformation components
│   └── load/                     # load data into database
└── [other_universities]/         # Other university connectors
```

## Connector Interface

Each connector implements the `BaseConnector` interface with the following methods:

```python
class BaseConnector:
    """Base class for all university data connectors."""
    
    name = "base"  # Override with university code
    
    def extract(self) -> dict:
        """
        Extract raw data from source.
        Returns a dict with raw data payloads.
        """
        raise NotImplementedError
        
    def transform(self, raw: dict) -> dict:
        """
        Transform raw data into universal schemas.
        Returns normalized dict with standardized data.
        """
        raise NotImplementedError
        
    def load(self, norm: dict) -> None:
        """
        Prepare data for loading into database.
        """
        raise NotImplementedError
```

## Available Connectors

### University of Guelph (UoG)

The UoG connector extracts course and program data from the University of Guelph website. It includes:

- Web scrapers for course and program data
- Transformers for converting to universal schemas
- Advanced prerequisite parsing for complex course requirements

For more details, see the [UoG connector documentation](uog/README.md).

## Adding a New Connector

To add a new university connector:

1. Create a new directory under `connectors/` with the university code
2. Implement the `BaseConnector` interface in a `connector.py` file
3. Create the necessary extraction and transformation components
4. Add documentation in a `README.md` file

## Universal Schemas

All connectors transform data into these standardized schemas:

### Universal Course Schema

```json
{
  "courseId": "SUBJ*1000",
  "courseCode": "SUBJ*1000",
  "title": "Course Title",
  "description": "Course description text...",
  "department": {
    "deptId": "SUBJ",
    "code": "SUBJ",
    "name": "Department Name",
    "parentId": null
  },
  "level": 1000,
  "credits": 0.5,
  "prerequisites": {
    "type": "AND|OR|COURSE|NOF|...",
    "courses": ["SUBJ*1000", "..."],
    "expressions": [...]
  },
  "corequisites": [...],
  "antirequisites": [...],
  "termsOffered": [...]
}
```

### Universal Program Schema

```json
{
  "programId": "PROG",
  "code": "PROG",
  "title": "Program Name",
  "type": "Major|Minor|Certificate|...",
  "degree": "Bachelor of Science",
  "description": "Program description...",
  "requirements": {
    "core": [...],
    "electives": [...],
    "credits": 20.0
  }
}
```

## Development Guidelines

When developing connectors:

1. **Respect rate limits**: Include appropriate delays in web scrapers
2. **Handle errors gracefully**: Log errors and continue when possible
3. **Document assumptions**: Note any special cases or interpretations
4. **Write tests**: Include unit tests for critical components
5. **Follow the schema**: Ensure output conforms to the universal schemas

## Running a Connector

Connectors can be run individually for testing or as part of the full ETL pipeline:

```python
from connectors.uog.connector import UoGConnector

# Initialize the connector
connector = UoGConnector()

# Run the full ETL process
raw_data = connector.extract()
normalized_data = connector.transform(raw_data)
connector.load(normalized_data)

# Or run individual stages
raw_data = connector.extract()
# Inspect or save raw_data...
```