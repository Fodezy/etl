# ETL Project

A standalone, plugin‑based ETL engine for ingesting academic program & course data into a Postgres database. Designed to scale from a handful of connectors (e.g., UoG, Bishops, MockSchool) to hundreds of bespoke pipelines, with schema‑validated transforms and versioned loading.

---

## Repository Layout

```text
etl-project/
├── connectors/                # Individual connector plugins
│   ├── uog/                   # University of Guelph connector
│   │   ├── README.md          # UoG connector documentation
│   │   ├── connector.py       # UoGConnector implementing BaseConnector
│   │   ├── extract/           # Web scraping components
│   │   │   ├── driver.py      # Orchestrates all scraping stages
│   │   │   ├── parsers/       # Data cleaning parsers
│   │   │   └── scrapper_modules/ # Reusable scraping modules
│   │   ├── transformers/      # Data transformation components
│   │   │   └── src/           # Prerequisite parsing logic
│   │   ├── raw/               # Raw extracted data
│   │   └── cleaned/           # Transformed data in universal schema
│   │
│   ├── bishops/
│   │   └── connector.py       # BishopsConnector
│   └── mockschool/
│       └── connector.py       # MockSchoolConnector (demo)
├── core/                      # ETL engine core
│   ├── connector_base.py      # Defines BaseConnector interface
│   ├── runner.py              # Discovers & orchestrates connectors
│   └── loader.py              # DB versioning & upsert logic
├── schemas/                   # Shared JSON‑Schema definitions
│   ├── universal_program.json
│   └── universal_course.json
├── tests/                     # Unit & integration tests
│   ├── fixtures/              # Sample HTML/JSON for extract & transform
│   ├── test_core.py           # Core discovery & runner tests
│   └── test_uog.py            # UoG connector tests
├── requirements.txt           # Python dependencies
├── .gitlab-ci.yml             # CI: lint, test stages
└── README.md                  # This document
```

---

## Prerequisites

* Python 3.9+
* PostgreSQL instance for loader tests & production
* `psycopg2-binary`, `jsonschema`, `pytest`, `black`, `isort`

---

## Installation

```bash
git clone <your-gitlab-url>/etl-project.git
cd etl-project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Core Components

### 1. connector\_base.py

Defines an abstract `BaseConnector`:

```python
class BaseConnector(ABC):
    name: str                # Unique connector name

    @abstractmethod
    def extract(self) -> dict:
        # Dump raw JSON/HTML from source

    @abstractmethod
    def transform(self, raw: dict) -> dict:
        # Normalize & validate against JSON‑Schema

    @abstractmethod
    def load(self, norm: dict) -> None:
        # Insert into DB (Type‑2 SCD for programs;
        # upsert for courses)
```

### 2. runner.py

Automatic discovery & execution of connectors:

* Scans `connectors/` directory via `pkgutil`.
* Imports each `connector.py`, instantiates subclasses of `BaseConnector`.
* CLI flags:

  * `--connectors uog bishops` → run only specified connectors
  * (no flag) → run all discovered connectors
* Orchestrates: `extract() → transform() → load()` for each.

```bash
python core/runner.py --connectors uog bishops
```

---

## Loader Deep Dive

`core/loader.py` handles all database interactions:

1. **Connection Management**: Open/close Postgres with `psycopg2` or an ORM.
2. **Type‑2 SCD for Programs**:

   * On each run, compare incoming `programId`:

     * If new → insert with `version=1`, `effective_date=NOW()`, `end_date=NULL`.
     * If changed → set previous row’s `end_date=NOW()`, insert new row with incremented `version`.
3. **Upsert for Courses**:

   * Use `ON CONFLICT(courseId) DO UPDATE` to merge changes.
4. **Raw Payload Audit**:

   * Optionally store the original JSON blob in an audit table for traceability.
5. **Transactions & Error Handling**:

   * Wrap load operations in transactions; rollback on failure.

---

## Scheduling (Optional)

While this ETL lives in its own repo, you’ll typically orchestrate runs externally:

* **Airflow**:

  * Define a DAG that invokes `core/runner.py` via a `PythonOperator`.
  * Tag tasks by cadence: `@monthly` for UoG/Bishops, `@weekly` for mocks.
  * Example DAG:

    ```python
    with DAG(..., schedule_interval='@monthly'):
        run = PythonOperator(
            task_id='run_etl',
            python_callable=run_all,
            op_kwargs={'connectors':['uog','bishops']},
        )
    ```
* **Prefect**:

  * Create a flow wrapping `runner.run`, parameterized by connector list.
  * Schedule with a `CronSchedule` or `IntervalSchedule` per connector.

These deployment configs live in your infra repo or orchestration project—kept separate from the ETL code.

---

## Testing & CI

* **Unit Tests**: Validate `extract`, `transform`, `load` logic using fixtures.
* **Integration Tests**: Spin up a test Postgres (via `pytest-postgresql`) to verify SCD/upsert.
* **Formatting**: `black`, `isort` enforced by CI

`.gitlab-ci.yml` stub:

```yaml
stages:
  - test

etl_test:
  image: python:3.10
  before_script:
    - pip install -r requirements.txt
  script:
    - black --check .
    - isort --check .
    - pytest -q
```

---

## Adding a New Connector

1. Create `connectors/<school>/connector.py` subclassing `BaseConnector`.
2. Implement `extract()`, `transform()`, `load()`.
3. Add unit & transform tests in `tests/test_<school>.py` with fixtures.
4. Update CI if you need extra dependencies (e.g., `beautifulsoup4`, `playwright`).

## Existing Connectors

### University of Guelph (UoG)

The UoG connector extracts course and program data from the University of Guelph website. It follows the standard ETL pattern:

1. **Extract**: Web scraping of course catalog and program information
2. **Transform**: Conversion to universal schema with specialized prerequisite parsing
3. **Load**: Database loading (currently stubbed)

Key features:
- Multi-stage extraction process with parallel execution
- Advanced prerequisite parsing using grammar-based parsing
- Comprehensive data cleaning and normalization

For more details, see the [UoG connector documentation](connectors/uog/README.md).

---

## Contributing

1. Fork the repo & create a feature branch.
2. Write tests for new behavior.
3. Follow `black` & `isort` formatting.
4. Open a merge request against `main`.

---
