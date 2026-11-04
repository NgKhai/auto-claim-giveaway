# Independent acceptance — AUTH-01a account privacy

Reviewed 2026-11-05. Accept the local sandbox account export/deletion increment on the evidence below. Production release remains unaccepted.

## Executed evidence

1. Before implementation, the independent API run had 18 tests: the 14 previous acceptance tests passed and all 4 new privacy tests failed at the expected missing endpoints (404). These tests exercised absent behavior.
2. The final QA-executed `python3 -m unittest discover -s tests -v` run completed with **30/30 passing**, 3.858 seconds: 19 independent API acceptance tests and 11 developer workflow tests. This included owner-scoped authentication throttle cleanup. Subsequent implementation changes require their own integration run; use the root integration run for the latest revision's total.
3. `python3 docs/quality/browser_smoke.py` passed in real Chromium after privacy UI/password-error handling and metadata changes were saved. The existing registration journey remained covered. Privacy assertions downloaded and parsed actual JSON, checked the filename and owner data/no authentication fields, cancelled deletion without losing the session, verified the password field cleared on reopening, rejected a wrong password while keeping dialog/workspace/session, deleted with the current password and observed old-account login return 401. No JavaScript errors occurred.

The browser script uses a temporary database and localhost process; test credentials are synthetic. Optional Playwright/system Chromium prerequisites are documented in RELEASE-REVIEW.md. Browser execution is not currently a CI gate.

## Independent API acceptance

- Export requires authentication and includes only the current account's profile, goals, applications and audit records. A second account cannot export the first account's email, private goal or application. Export omits password/hash, raw session token, CSRF token and internal approval authorization hash.
- Deletion requires the authenticated account's CSRF token and correct current password. Wrong password, missing CSRF, cross-origin mutation and anonymous requests are rejected without deleting account data.
- Deletion removes the owner's user, sessions, goals, applications and audit rows. Every active session for that owner becomes invalid. Another account and its goal remain usable. Previous credentials of the deleted account cannot log in.
- Fault injection installs a SQLite trigger that aborts final user deletion. The API returns 500, and owner user/session/goal/application/audit rows retain their previous counts. The original session remains usable, demonstrating atomic rollback for this injected database failure.
- Owner-tagged authentication throttle metadata is removed while another owner's throttle records remain, as covered by the developer regression executed with the final independent suite.

## Review and limits

Export/deletion owner IDs derive from the server session rather than client input. Export queries explicitly scope owner IDs. Deletion uses one transaction; successful deletion clears the session cookie. Password reauthentication uses the stored salted password derivation and constant-time comparison. Incorrect deletion-password responses display an actionable error without discarding a valid session.

This demonstrates logical deletion from active SQLite tables, not forensic erasure of free pages, historical backups or logs. Backup retention and restored-data deletion workflows remain production policy/operations gates. Verified identity, password reset, full profile editing and configured retention remain incomplete. This increment does not complete the entire AUTH-01 backlog task or establish production readiness.

Independent code-review findings are recorded separately in PRIVACY-CODE-REVIEW.md.
