# Independent privacy slice code review

Reviewed 2026-11-04 UTC against baseline `a43f9e5`, the local account export/deletion task and `docs/product/PRIVACY.md`. Scope: changes to `hunter/app.py`, `web/`, privacy regression tests and the privacy contract. No application code was changed by this reviewer.

## Scoped verdict

Accept the local privacy slice once the final QA API/browser results are recorded for the saved files. No unresolved critical/high security defect was identified. This adds local data controls; it does not complete production authentication, retention operations, third-party deletion or backup erasure.

The server derives ownership exclusively from the authenticated session. Export selects owner-scoped profile/goals/applications/activity and excludes password material, sessions, CSRF and approval hashes. Schema version and UTC export time are present. The existing API no-store response policy applies.

Deletion requires authentication, the session CSRF token, same-origin policy and current-password verification. One `BEGIN IMMEDIATE` transaction deletes the owner's applications, goals, audit, every session, profile and associated rate-limit rows. Other owners' data and sessions are outside its predicates. The requesting cookie is cleared after successful commit. Concurrent sandbox execution/deletion uses the existing serialized database boundary.

The UI separates opening settings, opening the warning, cancelling, and final password-confirmed deletion. Only the final form submits deletion. Export downloads server JSON through a Blob, without rendering it as HTML. Successful deletion clears client state and returns to authentication; modal dismissal clears the password. The warning scopes deletion to this application and excludes external provider accounts.

## Findings and fixes

| Finding | Severity | Disposition |
| --- | --- | --- |
| Wrong deletion password returned 401 and the generic API handler immediately signed the user out and closed the confirmation | Medium UX/acceptance defect | Fixed: only the exact authenticated deletion reauthentication-failure response bypasses generic session logout; invalid sessions still sign out. Final code inspected; QA should assert wrong-password modal persistence |
| Export lacked schema/version and export time required by the privacy contract | Medium acceptance defect | Fixed and independently verified: `schema_version: 1`, timezone-aware `exported_at` |
| Account deletion retained login-throttle rows associated with the owner's known account | Medium privacy acceptance defect | Fixed for attributable rows: additive `login_limits.user_id` migration, attribution on new known-user failures, and owner-scoped erasure; other owners' rows retained |

Pre-migration throttle hashes and failures for nonexistent accounts can have NULL ownership. They cannot be reliably associated with a deleted account. Their keys are pseudonymous hashes, not a guarantee of anonymity: knowledge of the email/IP combination can confirm a match. Current code deletes expired throttle rows opportunistically on login/deletion after the 15-minute window; it does not run a scheduled physical cleanup while idle. The privacy contract must disclose this legacy/security-data boundary rather than promise immediate removal of all historical hashes.

## Independent evidence

The reviewer ran a targeted fault-injection probe with a temporary SQLite database and a `BEFORE DELETE ON users` trigger that raises an abort. This fails after dependent-row deletion statements have run. Result: deletion returned **500**, all user/session/goal/application/audit row counts remained unchanged, and the original session still returned **200** from `/api/me`. This independently demonstrates transaction rollback on partial storage failure. The same probe verified export schema version and ISO UTC timestamp.

Dynamic checks required approved execution outside restricted IPC, as documented for the initial increment. No live provider, message or production account was involved.

The API tests cover owner-only export, recursive secret exclusion, unauthenticated denial, missing CSRF, foreign Origin, wrong password, all-session invalidation, other-owner preservation and stored-row deletion. The reviewer inspected these tests and the implementation; final suite/browser execution and exact counts belong in QA's recorded evidence. Opening/cancelling the final dialog must leave data intact; wrong password must retain the authenticated view; successful confirmation must leave old sessions unusable after reload.

## Release limits

SQLite logical deletion does not establish forensic secure erasure of database pages, operational backups or external copies. Production backup expiration, restore-time deletion reconciliation, legal/security retention policy, hosted identity hardening, deployment and monitoring remain separate gates. No claim of third-party deletion or production privacy compliance follows from this local slice.
