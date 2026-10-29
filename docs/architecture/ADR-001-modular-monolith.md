# ADR-001: Modular Python application with explicit execution boundaries

Status: selected for initial implementation, 2026-10-29.

The repository initially contained research documentation only; there was no build or test suite. The product owner delegated stack selection and autonomous implementation in MASTER_REQUIREMENTS.md.

## Decision

Use Python 3.12+, FastAPI, Jinja server-rendered HTML, sqlite3 persistence and pytest/httpx verification. Keep identity, opportunity catalog, policy, applications, audit and integrations as separate responsibilities within one deployable application. Use Playwright for controlled browser acceptance tests and eventually reviewed provider adapters.

SQLite supports a single-instance initial deployment and transactional uniqueness. It is not a claim of multi-region or horizontally scaled readiness. Move to PostgreSQL with migration and concurrency tests before multi-instance deployment. Session and policy checks stay server-side. No arbitrary LLM-generated code may execute in registration workers.

## Alternatives

TypeScript with an agent SDK and Playwright is viable but adds no immediate benefit over the available Python environment for this first slice. A microservice architecture adds distributed state and deployment complexity before there is evidence it is needed. A universal browser agent would broaden the validation surface before provider permission and receipt contracts exist.

## Consequences

The first increment must work without external credentials using clearly labeled sample opportunities. Sample data and local application intents must never be presented as live discovery or completed provider registrations. The broader product still requires live source connectors, semantic relevance, controlled browser execution, background monitoring, external notifications and operational acceptance. Their absence blocks a production-ready release, not local development.

Secrets come from runtime configuration, never repository files. Production requires HTTPS, secure cookies, a durable data volume, backup/restore verification and hosting credentials. All irreversible provider actions require current deterministic authorization and an adapter permitted by the provider.
