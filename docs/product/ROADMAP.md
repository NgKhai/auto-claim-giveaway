# Roadmap and Prioritized Backlog

Owner: PM. Baseline: 2026-10-29. Requirements: [PRD](PRD.md). Status values: planned, in progress, blocked, verified, done. Done requires the common gate below and a recorded commit/push; this planning document makes no completion claims.

## Milestones

| Milestone | User-visible deliverable | Exit gate |
| --- | --- | --- |
| M1 — First complete journey | Profile/goal, opportunity evidence, policy decision, application tracking and audit in a running web app | Auth boundaries and positive/negative API/UI journey tests; QA review; persisted restart check; pushed increment |
| M2 — Live discovery and model interpretation | Permitted-source ingestion, normalization, semantic relevance and stale-data handling | Real provider/model verification where configured; fixture vs live distinction; bounded failures and injection tests |
| M3 — Controlled execution | Concrete approvals and reviewed browser adapter with takeover/reconciliation | Controlled-browser E2E plus permitted-provider validation; revocation, duplicates and changed-form tests |
| M4 — Monitoring and privacy | Durable follow-up, notification channels, export/deletion and operational controls | Delivery/failure/restart tests, privacy review and credential-scoped live verification |
| M5 — Release acceptance | Deployable, observed and recoverable service | CI evidence, load baseline, deployment/rollback/restore verification and independent QA + PM sign-off |

## Common Definition of Done

Every task must meet its acceptance criteria, pass relevant tests, receive independent QA review and PM product acceptance, have no unresolved high/critical defect in its scope, update documentation, and be committed/pushed with remote confirmation. Record test commands/results, review findings, commit SHA and push status in project progress. A planned test is not a passed test. Split a task further if it cannot be independently verified in one increment.

## Backlog

| ID / priority | Owner / dependencies | Deliverable and acceptance | Technical considerations | Required checks |
| --- | --- | --- | --- | --- |
| T01 / P0 | Lead + BA; none | Agree PRD/SRS, ADR, plan and traceable release gates; unknown external prerequisites documented | Existing research preserved; one coherent stack | Cross-review requirements and contract consistency |
| T02 / P0 | Dev; T01 | Bootable app, migration mechanism, isolated user access and persisted profile | Single-instance SQLite; safe session handling; configuration validation | Startup/health, migration repeatability, auth and ownership tests |
| T03 / P0 | Dev; T02 | Create/view goals with validated input and useful empty states | Persist ownership; bounded query/input lengths | Goal API tests, persistence and cross-user denial |
| T04 / P0 | Dev; T03 | Evidence-backed opportunity list/details and application request | Fixtures clearly marked; do not imply live freshness | UI/API journey, escaping, evidence provenance and empty/error states |
| T05 / P0 | Dev; T04 | Deterministic allow/review/block decisions and audit | Domain/action/data scopes, freshness, eligibility and expiry; no trust-score authorization | Policy matrix, revoked permissions, contradictory/missing evidence, expired/country mismatch |
| T06 / P0 | Dev; T05 | Persist applications, concrete approval and manual takeover states | Unique user/campaign action; approval fingerprint; no fabricated receipt | Duplicate/concurrency tests, approval ownership, payload change and restart |
| T07 / P1 | Dev AI; T04 | Permitted-source ingestion with normalization/deduplication and freshness | Allowlist, redirect/DNS defenses, limits/timeouts; source terms tracked | Connector fixtures, invalid/oversized data, injection, rate-limit and failure recovery |
| T08 / P1 | Dev AI; T07 | Goal interpretation and semantic matching with explicit deterministic fallback | Credential optional locally; structured model output cannot grant rights | Malformed model output, no-key fallback, semantic relevance evaluation and live check when available |
| T09 / P1 | Dev Automation; T06,T07 | Reviewed browser adapter and bounded handling of changed fields | Provider terms and user authorization required; no credential/financial auto-submit | Browser form E2E, unauthorized fields, CAPTCHA/auth takeover, redirects and ambiguous outcomes |
| T10 / P1 | Dev; T09 | Recovery and reconciliation of interrupted submissions | Claim-before-submit; do not equate DB uniqueness with external exactly-once | Competing workers, crash/timeout after send, receipt reconciliation and no blind retry |
| T11 / P1 | Dev; T06 | Durable monitoring and in-app notifications | Timezone-aware scheduling; bounded retries and idempotent events | Expiry/reminders, restart, disabled automation and duplicate notification tests |
| T12 / P1 | Dev Integrations; T11 | Email/Discord adapters with delivery status | Authorized credentials and scopes; no unrequested messages during setup | Adapter contract, transient/permanent failure, deduplication and configured live delivery |
| T13 / P1 | Dev; T02,T06 | Data export/deletion, preference changes and automation stop | Retention, audit minimization, session invalidation and pending-job cancellation | Ownership, export safety, deletion consistency and revoked-job tests |
| T14 / P0 before release | DevOps + QA; T02 onward | CI lint/type/test/build, deploy artifact, health/monitoring and recovery runbooks | Secret-free config; development/production separation; rollback compatibility | CI run evidence, clean install, backup restore, rollback and load baseline |
| T15 / P0 before release | QA + PM; T07–T14 | Release acceptance report with full coverage and unresolved blockers | No production claim while live critical journeys or operational gates remain unverified | Realistic end-to-end regression, security review, PM acceptance and release decision |

## Product review protocol

For each increment PM checks the user can understand the result, distinguish unsupported/manual work from completed registration, inspect evidence and find the next action. QA independently checks requirements coverage and records failures. BA reconciles acceptance criteria with the shipped contract. Root integrates reviewed changes and updates the shared progress record.

## Continuation and external blockers

Do not wait for credentials to implement contracts, local UI, deterministic controls, failure handling or tests. Track unverified live integrations explicitly and move to independent tasks. Request only the exact credential/hosting/provider prerequisite after inspecting available bindings; never ask for secret values in chat. A provider prohibition is not solved by adding credentials.
