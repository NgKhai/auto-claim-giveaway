# Opportunity Platform Implementation Plan

> For agentic workers: use subagent-driven development with independent QA review. User explicitly authorized autonomous technical decisions and implementation; routine confirmation is not required.

**Goal:** Deliver and verify successive complete user journeys toward the master product requirements.

**Architecture:** Modular FastAPI application with server-rendered UI, persistent account-scoped state and deterministic policy. Provider actions remain distinct from local tracking.

**Tech Stack:** Python, FastAPI, Jinja, sqlite3, pytest/httpx; browser validation with Playwright when available.

**Spec:** `docs/product/MASTER_REQUIREMENTS.md`, with PRD/SRS elaboration.

## Global constraints

- Never bypass CAPTCHA, authentication, rate limits or provider restrictions.
- Never submit sensitive credentials or financial information automatically.
- Never claim production readiness without verified evidence.
- Preserve user changes, test increments, use Conventional Commits, push verified work.
- No LLM-generated trust score alone can authorize sensitive operations.

## Review focus

Cross-user resource access must fail; CSRF must reject forged mutations; revoked authorization must be effective at execution; duplicate attempts must not duplicate provider submission; sample data must never imply a real reward or registration.

## Tasks

- [ ] P0 — PM/BA: produce PRD, SRS, contracts and roadmap; reconcile with actual implementation.
- [ ] F1 — Dev: account/session lifecycle, goal/profile persistence and catalog discovery. Write failing auth/validation/isolation tests, implement, run full suite. Files: app modules/templates, requirements.txt, tests.
- [ ] F2 — Dev: deterministic eligibility and action permission, application intent, approval/revocation, audit and in-app notifications. Test expired/unknown/restricted opportunities, duplicate intents and tenant ownership before implementation.
- [ ] Q1 — QA: independently exercise F1/F2, report reproducible defects, retest fixes. File: tests/test_security_review.py; quality report records exact commands and outcomes.
- [ ] O1 — Root: startup documentation, CI, container/deployment configuration and backup/rollback procedures. Verify install, HTTP health and representative journey locally; identify unavailable external deployment prerequisites.
- [ ] R1 — PM + QA + root: review scope versus master requirements, persist defects and backlog, commit/push verified increment and verify remote SHA.
- [ ] F3 onward — select next dependency-ready tasks from roadmap: live discovery and evidence; semantic relevance; reviewed browser adapter; monitoring; notifications; privacy and release operations. External prerequisites remain explicitly blocked until supplied and tested.

## Execution ledger

Initial baseline: commit 3fb4483, seven research documents, no executable application or test suite. Working branch: feat/opportunity-platform. PM, BA, Dev and independent QA workstreams dispatched with nonoverlapping file ownership. Root performs integration and release verification.
