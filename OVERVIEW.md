- **Discovery & Selection**
  - `runner.py --connectors uog,bishops`
  - Or: `runner.py --all` or `--because tags=“mock,prod”`
- **Scheduling**
  - Hook into Airflow/Prefect DAGs that read a config list of active connectors; schedule each on its 4-month or weekly cadence.
- **Versioning Logic** (in loader.py)
  - **Programs**: write as Type-2 SCD—new row with `version`, `effectiveDate`, `endDate=null`.
  - **Courses**: SCD-1 style—upsert on `courseId`.
- **Pros**
  - One codebase, one CI pipeline, shared utilities.
  - Easy “new school” onboarding: drop folder + add to config.
- **Cons**
  - Repo grows—mitigate with clear naming & archiving old connectors.

---

## 2. Workflow Orchestration with a Scheduler

Instead of hand-rolling cron scripts, use a lightweight orchestrator:

- **Airflow**
  - Dynamically generate DAGs from your connector registry.
  - Tag DAGs by frequency (e.g. `@monthly`, `@weekly`).
  - Clear UI for “run this connector now” or retry fails.
- **Prefect** (or Luigi)
  - Similar plugin support with Pythonic flows.
  - Built-in parameterization (`flow.run(connectors=["uog","mock"])`).
- **Why it helps**
  - Centralized monitoring, retries, SLA alerts.
  - Configuration for “only run these two” without custom scripting.

---

## 3. Microservice-Style Deployment (Midterm Scale)

Once you exceed ~10–15 connectors or need isolated ops:

- **One Docker image per connector**
  - Contains only that school’s code + shared SDK.
  - Push to a Docker registry; deploy via Kubernetes/Cloud Run.
- **Connector API** (optional)
  - Expose `/run` and `/health` endpoints.
  - ETL core (or orchestrator) triggers each via HTTP.
- **Service Mesh**
  - Use tagging/labels to select which connectors to run in a given release.

---

## 4. Testing Strategy

You’ll need layered tests for every connector:

1. **Unit tests** for `extract()` with canned HTML/PDF fixtures.
2. **Transform tests** using small raw JSON samples → assert match against universal JSON Schema .
3. **Loader tests** (pytest + a test Postgres):
   - First ingest → tables populated.
   - Re-run with a change → proper SCD2 row created for programs, upsert for courses.
4. **End-to-end CI**: spin up a Postgres service in GitLab CI, run `runner.py --all`, then hit your REST API and confirm record counts.

---

## 5. Data Versioning & Schema Mapping

Your universal schemas define exactly what transform() must output:

- **Program Schema** (`universal_program.json`):
  - `programId`, `code`, `name`, `programTypes` (e.g. “Major”), `totalCredits` required fields :contentReference[oaicite:1]{index=1}.
- **Course Schema** (`universal_course.json`):
  - `courseId`, `courseCode`, `title`, `credits` plus nested `sections[]`, `termsOffered[]` :contentReference[oaicite:2]{index=2}.

Use a JSON-Schema validator in your transform step to catch drift.

---

## Recommendation & Roadmap

1. **Start with Option 1 + Orchestrator**
   - Build your monorepo plugin pattern
   - Wire in Airflow/Prefect immediately for scheduling and ad-hoc runs
2. **Implement robust loader logic**
   - Type-2 SCD for programs; upserts for courses; record raw payload for auditing.
3. **Lock in test harness**
   - Parameterize connector tests; add GitLab CI stage with Postgres service.
4. After 10–15 connectors, **spin out heavy/hard‐to‐maintain ones** into microservices (Option 3).

This hybrid path gives you minimal operational overhead at first—while still scaling cleanly to hundreds of connectors, with versioning, selectable runs, and full test coverage baked in.
