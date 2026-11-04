# Roadmap and shared backlog

Status: planned requirements, 2026-11-05. Progress, commands/results, commits and push status must be recorded separately from these acceptance definitions. No row is Done merely because it appears here.

## Definition of Done

For each functional increment: acceptance passes, relevant automated tests run, independent QA review completed, blocking defects fixed and retested, affected regression passes, security boundaries reviewed, documentation current, focused Conventional Commit created and pushed when remote access permits. When push fails, retain the local commit and report the precise error. Production release additionally requires realistic integration tests, CI, deployment/rollback and backup/restore evidence and PM/QA acceptance.

## Prioritized work

| ID / priority | Owner / dependencies | Deliverable and technical considerations | Acceptance criteria and required tests |
| --- | --- | --- | --- |
| FND-01 / P0 | PM + BA / none | PRD, SRS, roadmap; separate sandbox and full product | Requirements trace to acceptance; QA reviews omissions and contradictions |
| FND-02 / P0 | Dev / FND-01 | ADR, modular FastAPI/SQLite local application, repeatable setup and CI | Clean environment can install/start; health and automated checks run; no secrets committed |
| DISC-01 / P0 | Dev / FND-02 | Goal creation and curated fixture search with evidence | Valid/invalid/empty-result cases; fixture marker visible; matching reason and evidence readable |
| POL-01 / P0 | Dev + BA / DISC-01 | Deterministic allow/review/deny engine | Expiry, country, forbidden data, unknown facts and provider prohibition tests; LLM output cannot authorize |
| APR-01 / P0 | Dev / POL-01 | Exact-action approval and revocation | Mutated payload, version, destination, expiry and revoked approval rejected at execution; no side effects |
| REG-01 / P0 | Dev / APR-01 | Reviewed sandbox registration and durable receipt | Successful approved journey; repeated execution produces one receipt; sandbox success explicitly labeled |
| TRK-01 / P0 | Dev / REG-01 | Persistent application list and structured activity | Restart preserves result; audit explains decision; receipt does not imply reward approval |
| QA-01 / P0 | Independent QA/QC / DISC-01–TRK-01 | API/UI journey, security and persistence review | Acceptance report lists executed/failed/skipped checks and defects; blockers fixed/retested before milestone acceptance |
| REL-01 / P0 | Orchestrator / QA-01 | Verified local increment and progress record | Test evidence, review disposition, commit hash and push result recorded; pending scope visible |
| AUTH-01 / P1 | Dev + QA / REL-01 | Hosted identity, account isolation, profile controls | Authentication/session/CSRF protections as applicable, cross-user denial, revocation and deletion tests |
| SRC-01 / P1 | Dev + BA / AUTH-01 | Allowed live-source registry and bounded ingestion | Permission records, freshness/contradiction states, SSRF/redirect/DNS and malicious-content tests pass |
| AI-01 / P1 | AI Dev + QA / SRC-01 | Structured intent/extraction and semantic matching; fallback when AI unavailable | Reviewed labeled dataset; evidence grounding and unknown-state evaluation; model output cannot grant tool access |
| WEB-01 / P1 | Automation Dev + QA / SRC-01, APR-01, AUTH-01 | Provider-specific browser adapters with handoff | Real provider automation permission documented; DOM drift, unexpected fields, auth/CAPTCHA and redirect cases tested |
| REC-01 / P1 | Dev + QA / WEB-01 | Worker orchestration, idempotency and uncertain-outcome reconciliation | Concurrent workers, restart during submit, timeout-after-submit and provider outage tests; no blind resubmit |
| MON-01 / P1 | Dev / REC-01 | Deadline/status scheduler and pause controls | Explicit timezones, revoked permission, restart and duplicate jobs verified |
| NOT-01 / P1 | Dev + QA / MON-01 | In-app, email and Discord delivery | Authorized configured destinations only; deduplication, retry bounds, outage and honest delivery outcomes tested |
| OPS-01 / P1 | DevOps + QA / AUTH-01, REC-01 | Production database, migrations, deployable artifacts, health/errors, secrets | Migration rehearsal, backup restore, rollback and monitoring drills recorded; no invented hosting success |
| SEC-01 / P0 release gate | Independent QA/QC / AUTH-01–OPS-01 | Threat-model review, security regression and measured load tests | Critical/high findings resolved; workload and measured limits documented; external checks distinguished from local tests |
| REL-02 / P0 release gate | PM + QA/QC / SEC-01 | Production release acceptance | All essential journeys and required integrations pass realistically; CI and operations evidence current; no unresolved release blockers |

P0 release gates apply before production, even where their dependencies are later work. P1 means ordered after the first sandbox increment, not optional full-product functionality.

## First increment task sequence

### AUTH-01a: next local privacy slice

Priority P1; owner Dev, independent reviewer QA/QC; dependencies REL-01 and existing account/session/CSRF controls. Status: specified; implementation and verification pending. Deliver own-data JSON export and password/CSRF-protected atomic local account deletion with explicit browser consent. Acceptance and required tests are [PRIVACY.md](PRIVACY.md), PRIV-01–09. Apply the shared Definition of Done; passing this slice does not complete production authentication, retention or backup operations in AUTH-01/OPS-01.

FND-01 → FND-02 → DISC-01 → POL-01 → APR-01 → REG-01 → TRK-01 → QA-01 → REL-01. PM and BA check each task against the SRS; Dev and QA exchange defects and retest results. Independent review must be an actual separate review, never a renamed self-check.

## Required progress record fields

For each task record status (`planned`, `in_progress`, `blocked`, `review`, `verified`, `done`), owner, changed files, acceptance evidence, executed commands and outcomes, defects and retests, reviewer, commit SHA, push destination/result, current risks and next task. Record external blockers with exact missing operation/configuration; do useful independent work before requesting credentials or infrastructure. Never store secret values.

## Initial known risks

- Repository began as research only: no baseline runtime or test suite existed.
- Existing GitHub proxy connectivity failed during onboarding; test the current operation before reporting push availability.
- Live provider permission, AI credentials, notification destinations and hosting are not established by bundled fixtures.
- Sandbox tests cannot validate live website behavior, production isolation, scale or operational readiness.
