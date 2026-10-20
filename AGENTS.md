# Legal-Lens Repository Conventions & Agent Guidelines

## 1. System Architecture
- **Monorepo Layout**:
  - `backend/`: FastAPI Python application (Python 3.11+).
  - `frontend/`: Next.js 16+ (App Router, React 19) web client.
  - `docs/`: Architecture, schemas, and specifications.

## 2. Module Ownership & Isolation Rules
- **Knowledge-Graph Pipeline (Protected)**:
  - Do NOT modify files under `backend/app/{ingestion,extraction,resolution,validation,temporal,review,storage,llm,schema}`.
  - Import from them strictly read-only if necessary.
  - Keep docket, core, and audit code completely independent of heavy ML libraries (`torch`, `docling`, `gliner`, `transformers`) to ensure tests run in milliseconds.
- **New Feature Packages**:
  - Put new backend code into dedicated packages: `backend/app/core`, `backend/app/audit`, `backend/app/docket`.
  - Module layout for each package: `schemas.py`, `models.py`, `service.py`, `router.py`, `tests/`.
  - **Dependency Rule**: Routers stay thin; business logic lives in `service.py`. Features may import platform modules (`core`, `audit`); platform modules must never import feature modules.
- **Main Application Modifications**:
  - The only existing file permitted to be touched is `backend/app/main.py`, solely to include aggregator routers (e.g., `app/api/v1.py`).

## 3. Multi-Tenancy & Access Control
- Every query and endpoint must be scoped to a `matter_id`.
- Access control requires `matter_members(user_id, matter_id, role)`. A user must never read or write another matter's data. Non-members receive HTTP 403 Forbidden.
- Reminders track `created_by`/`user_id`; notifications have recipient `user_id`, and notification queries return only the calling user's notifications.
- Cross-matter resource linking (e.g., attaching a document or reminder from a different matter) must be rejected with HTTP 400 or 404.

## 4. Database & ORM Conventions
- **SQLAlchemy 2.x**: Use `DeclarativeBase`, `Mapped`, and `mapped_column`.
- **Database Engine**: SQLite with foreign keys enabled for local dev; fully Postgres-compatible (no SQLite-only features).
- **Date/Time Handling**: Use a custom `UTCDateTime` `TypeDecorator` for all datetime columns (ensures timezone awareness as SQLite drops tzinfo). All timestamps stored in UTC.
- **Enums**: Use `String` with `CheckConstraint` instead of native database Enums for cross-database portability.
- **Audit Logs**: Append-only table (`audit_logs`) protected by database triggers blocking `UPDATE` and `DELETE`. `record_event()` must not commit itself; it writes within the caller's active database transaction.

## 5. Code Quality & CI Standards
- Backend code must pass:
  - `black --check .`
  - `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
  - `mypy`
  - `pytest`
- Tests must be isolated and execute fast.

## 6. Frontend Guidelines
- **Next.js Version**: Uses Next.js 16+ (refer to `node_modules/next/dist/docs/` for breaking changes and conventions).
- **Styling**: Inherits the brand palette and design language defined in `frontend/src/app/globals.css` (burgundy, gold, dark cream, dark card backgrounds).
- **Type Safety**: Generate typed clients from backend OpenAPI schema; never hand-write duplicate schema definitions.
