# Opportunity Hunter Implementation Plan

**Goal:** Implement and independently verify the first persistent end-to-end sandbox journey while maintaining the complete product backlog.
**Architecture:** Python modular web application, same-origin browser UI, transactional SQLite.
**Spec:** User master prompt and docs/product/PRD.md, SRS.md.

## Constraints
- Preserve research and user changes; use current isolated checkout.
- No real registrations, messages or fabricated evidence; sandbox records explicitly labeled.
- Every authenticated mutation requires CSRF; isolate every user's records.
- Approvals must be version-bound and execution rechecks policy. Repeated execution must not duplicate receipts.
- Do not describe partial sandbox release as production ready.

## Tasks
1. PM/BA: document full PRD, SRS, backlog and acceptance criteria; distinguish full target from first increment.
2. Backend: tests first for authentication, goal matching, evidence, policy denial, approval, revocation, idempotency, tracking and tenant isolation; implement hunter/app.py and tests/test_domain.py.
3. Frontend: build web/index.html, style.css and app.js against agreed /api contract; display evidence, states and explicit sandbox boundaries; user content rendered as text.
4. QA: independent API journey and adversarial regression tests in tests/test_api.py; communicate defects and rerun after fixes.
5. Integration: root README, pinned dependencies, CI and deployment instructions. Run unittest discovery, compile checks, JavaScript syntax, live HTTP smoke, independent review; fix and retest.
6. Commit verified increment and attempt push; record exact failures without claiming success. Continue release backlog as prerequisites permit.

## Review focus
Expired or conflicting evidence; stale approvals; duplicate execution; tenant isolation; browser/API errors and misleading demo claims.

## M2: local account privacy

Spec: docs/product/PRIVACY.md. After verified M1 commit/push, implement tests-first GET /api/account/export excluding credentials/session/CSRF secrets and POST /api/account/delete with password reauthentication and existing origin/CSRF boundaries. Transaction removes own profile/goals/apps/audit/sessions only. Add explicit browser export/download and deletion confirmation controls. Independent QA must test wrong-password/CSRF denial, other-account survival and all-session invalidation; reviewer checks data minimization and deletion boundaries. Update evidence and commit/push as a separate increment after full regression. Production retention and third-party deletion remain future requirements.
