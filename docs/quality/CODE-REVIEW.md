# Independent code review

Reviewed: 2026-11-04 UTC. Scope: the first local sandbox increment in ADR-001 and the implementation plan, assessed against PRD/SRS. This is a review of working-tree files before the integration commit, not a production security certification.

## Verdict

Accept the bounded local sandbox journey after the final integration checks. No unresolved critical/high defect was identified in this scope after the fixes below. The complete product and production release remain incomplete. In particular, this verdict does not mean all FR-01–10 data-model requirements or later milestones are delivered.

Reviewed `hunter/app.py`, domain/API tests, `web/index.html`, `web/app.js`, architecture, product requirements, test plan and operating instructions. The reviewer made no application-code changes.

## Findings and disposition

| Finding | Severity in initial slice | Disposition |
| --- | --- | --- |
| Approval lacked an expiry and could execute indefinitely across sessions | High | Fixed: persisted 15-minute expiry, checked at submit; independently verified expired approval returns 409 |
| Unmatched goal returned every fixture with zero relevance | Important acceptance defect | Fixed: nonempty query filters zero-relevance rows; independently verified an unmatched query returns `[]` |
| Approval binding omitted destination, action and adapter identity | High | Fixed: server fingerprint includes sandbox action, destination, adapter version and required fields; independently verified destination change returns 409 |
| Approval UI initially omitted action/destination/adapter | Important acceptance defect | Fixed: dialog now displays descriptor and payload and disables consent when descriptor is absent; code inspected |
| Expired/revoked application could never be renewed because of permanent unique application row | Medium | Fixed: repeat evaluation renews the same row with incremented version and cleared consent; regression test passes; UI offers reevaluation |
| Country option did not satisfy backend country validation | Medium | Fixed: option now uses the two-character `XX` unknown-country code |
| UNIX-second activity timestamps displayed as dates in 1970; recent lists reversed newest-first server ordering | Medium | Fixed: numeric timestamps converted to milliseconds; goal/audit order retained; code inspected |
| Expired session retained previous account's selected goal | Medium | Fixed: returning to authentication clears goal selection and pending approval; code inspected |

Origin protection was added during the review: unsafe requests with a mismatched Origin or cross-site Fetch Metadata are rejected, including unauthenticated login/register. Authenticated writes additionally require the session's CSRF token. Ownership checks apply to reads, approvals, submission and revocation. Cookies are HttpOnly and SameSite Strict; Secure cookies remain an explicit HTTPS deployment configuration.

SQLite `BEGIN IMMEDIATE` encloses ownership/policy checks, approval validation, receipt persistence and audit insertion. The user/opportunity unique constraint prevents duplicate application rows. This establishes local transactional idempotency for the sandbox executor; it cannot establish exactly-once delivery to external providers.

All dynamic user/source text uses `textContent` or DOM text nodes. Links restrict schemes and use `noopener noreferrer`. No raw HTML interpolation was found. The UI explicitly calls opportunities synthetic and receipts sandbox results, and does not imply provider approval or benefit fulfillment.

## Independent verification

- Current unittest suite: **22 tests passed**, including recovery, tenant isolation, CSRF, changed payload/descriptor, expiry, policy reevaluation and restart persistence.
- Additional reviewer concurrency check: **12 simultaneous submissions using 8 workers**, all HTTP 200, **one unique receipt and one submission audit event**.
- Additional reviewer probes: foreign-origin registration **403**; unmatched query **empty list**; expired approval submission **409**; changed destination after approval **409**.
- Final frontend syntax check: `node --check web/app.js` passed. Final action/expiry/recovery/time display changes were inspected directly.
- QA's separate browser exercise is recorded in its test report/script; this reviewer did not independently rerun the browser. Root integration must run the browser check against the final saved frontend.

The restricted tool sandbox caused FastAPI TestClient calls to hang. The reviewer reran dynamic checks with approved unrestricted IPC and temporary databases; those checks completed. This is an execution-environment limitation, not a claim that the API hung over real HTTP.

## Remaining boundaries

These are remaining product/release work, rather than blockers to the explicitly local synthetic journey:

- Catalog matching is lexical; semantic intent, labeled relevance evaluation and live-source evidence freshness/contradiction handling are absent. The fixture evidence is descriptive text, not the full normalized evidence/entity contract. Policy currently returns plain explanations rather than a complete structured reason-code model.
- There is no writable provider catalog or real adapter. Before introducing either, persist immutable action snapshots and require the reviewed action fingerprint at approval time: the current approve request carries only the application version and hashes the current in-process fixture descriptor. Runtime catalog edits between display and approval are outside this static-fixture scope.
- Account verification/reset/deletion, production abuse controls, fixed trusted-host/origin configuration, TLS, migrations, transitive dependency locking, deployment/restore drills and monitoring require their own acceptance. Origin comparison to the request host is not a substitute for production host configuration.
- Source fetching/SSRF controls, AI evaluation, provider automation permission, browser handoff, external unknown-outcome recovery, notifications and continuous monitoring remain unimplemented. No local test or sandbox receipt proves these capabilities.

The safe release description is a verified local sandbox increment, with the remaining production gates maintained in the backlog and operations documents.
