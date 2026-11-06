# Shared delivery progress

Updated 2026-11-05. Full product remains incomplete and is not production-ready.

## Current milestone

M4 AUTH-01b deployment configuration guards are in progress: explicit fail-closed production host/origin/database/cookie settings and HSTS, preserving development defaults. Design/implementation and independent verification remain pending; no deployment, final test count or release readiness is asserted. The lead owns the deployment-guards design and final evidence.

M3 SRC-01a fixed-source documentation retrieval is implemented and independently accepted in its scoped read-only workflow, commit `8528567`. The fixed registry entry is owner-scoped and separate from executable sandbox opportunities. Source eligibility/deadline/automation permission remain unknown. Owner export/deletion includes source records. Full general discovery, semantic extraction and arbitrary-source network safety remain unfinished.

M1 local sandbox journey and M2 local privacy increment implemented; M1 accepted by independent QA for its tested scope. PM/BA's two conditional UI findings (exact-action consent and Unix audit time rendering) are resolved and explicitly verified in Chromium. Existing research files remain unchanged.

| Workstream | State | Evidence |
| --- | --- | --- |
| PM/BA | Local slice reviewed; full target preserved | PRD.md, SRS.md, BACKLOG.md |
| Backend | Verified local slice | 22 regression tests, ownership/CSRF/policy/consent/persistence/concurrency |
| Frontend | Verified browser journey | Real Chromium signup → goal → exact consent → sandbox receipt → reload → mobile → logout |
| Independent QA | Local slice accepted; production rejected | ../quality/RELEASE-REVIEW.md |
| Independent code review | See reviewer verdict | ../quality/CODE-REVIEW.md |
| Integration | M1–M3 scoped increments accepted; M4 configuration guards in progress | CI configured; remote CI not yet observed |

## Verified evidence

- Initial baseline: seven research Markdown files, no runtime or test suite.
- Installation: Python venv using available system packages; pinned requirements satisfied. No TLS/checksum bypass.
- Lead final regression: `.venv/bin/python -m unittest discover -s tests -v`: 22 passed, 2.207 seconds. Independent QA also ran the suite and Chromium smoke. No coverage percentage is claimed.
- `node --check web/app.js`, Python compileall and `git diff --check`: pass.
- Live HTTP GET /api/health returned status ok, mode sandbox, external_registration_enabled false.
- Browser explicit assertions verify action, destination, adapter, 15-minute approval text and audit year derived from persisted timestamp; mobile viewport has no horizontal overflow.
- Concurrent submission returns one receipt and one submission audit event. This is a local SQLite guarantee, not external exactly-once delivery.
- TestClient emits an upstream deprecation warning for httpx; it is not a failing test. Restricted command sandbox IPC/network caused initial hangs/proxy errors; supported approved execution resolves both. Existing GitHub read authentication verified; no new token needed.
- Install/start instructions saved to environment draft; publication and fresh-task restoration not verified.

## Defects and disposition

Resolved and retested: unmatched goals returned unrelated fixtures; approvals lacked TTL and complete action descriptor; cross-origin login mutation; expired/revoked request renewal; account-switch retained UI state; Unix timestamps displayed 1970; consent modal omitted destination/action/adapter. QA corrected an early report sentence that preceded the UI fixes and reran with explicit assertions after those fixes landed.

No unresolved high defect identified in the tested local slice. This is not a comprehensive penetration test, load test or production certification.

## Commit and push evidence

M1 functional commit: `a43f9e5` (`feat: add verified opportunity hunter sandbox workflow`). `git push -u origin work` succeeded; no merge to main. Remote CI result remains unobserved. M2 privacy export/deletion verified and pushed as `6897ced`; final record below.

## Next prioritized tasks

AUTH-01a local privacy slice is implemented and independently accepted. See [PRIVACY.md](PRIVACY.md), [QA report](../quality/PRIVACY-REVIEW.md) and [code review](../quality/PRIVACY-CODE-REVIEW.md). Final regression: 30 tests passed; Chromium export/cancel/reauth/deletion and old-login denial passed. Atomic rollback under injected deletion failure and multi-IP throttle ownership were tested. Commit/push recorded below. Legacy unassociated pseudonymous throttle hashes and production backup/retention remain explicitly limited.

1. AUTH-01: account lifecycle/privacy (export/deletion/retention), Internet-facing auth hardening and abuse controls; add acceptance and independent security tests.
2. SRC-01: permitted live read-only source registry, bounded ingestion, freshness/conflict evidence and SSRF/redirect/DNS controls.
3. AI-01: structured intent/extraction and semantic relevance with labeled evaluations, credential configuration and honest unavailable fallback.
4. WEB-01/REC-01: reviewed provider adapters and explicit authorization, browser handoff, uncertain-outcome reconciliation and durable workers.
5. MON-01/NOT-01: scheduling, pause controls, deduplication and authorized email/Discord notifications.
6. OPS-01/SEC-01/REL-02: production storage/migrations, locked dependencies, container build, real deployment/CI, measured load, monitoring, backup restoration and rollback validation.

Live-provider permission, AI credentials, authorized notification destinations and hosting are not configured or verified. They block live integration/release checks, not the local development workflow. No emails, real registrations, awards or external deployment are claimed. Remaining software work is explicitly unfinished, not mislabeled as solely credential-blocked. Continue with AUTH-01, using the saved backlog and this record rather than rebuilding M1.

## M2 final integration

Node syntax, Python compile and git diff whitespace checks pass. CI Actions API read returned Forbidden while Git read/push works; remote CI remains unverified. M2 commit `6897ced` (`feat(privacy): add account export and verified local deletion`) pushed successfully to `origin/work`. Final root suite on the multi-IP revision: 30/30 pass, 3.749 seconds. Final root Chromium smoke passed with no JavaScript errors. Working application sources were not changed after these checks. No externally hosted product, provider integration, notification delivery or production readiness is claimed. Next work remains production auth/retention and SRC-01; implementation beyond the two local increments remains unfinished.

## M3 verified integration — 2026-11-06

SRC-01a fixed official source implemented and independently accepted within its read-only scope. Source evidence is separate from the synthetic executable opportunity catalog. Backend and QA tests cover transport bounds/deadline, unsupported compression, UTF-8, redirects, cooldown persistence/concurrency, owner isolation, freshness/change/error retention and privacy integration. Review fixed a slow-trickle total-timeout bug and UI freshness/account-switch regressions.

Lead final regression: 50/50 tests passed in 7.037 seconds; JavaScript syntax, Python compile and whitespace checks passed. Baseline Chromium M1/M2 and dedicated Sources Chromium both passed with no JavaScript errors. The latter uses deterministic fixtures, including hostile text and preserved evidence after errors.

Separate real-network check: authenticated API refresh over actual HTTPS returned 200 from the fixed official raw GitHub doc; hash `880671771eee701e5cff33ff4c8ba409c306e38039ea8a1bb6b9e5a9856db17a`, excerpt 3602 characters, fresh; immediate repeat 429, export contains one source. Eligibility/deadline/automation remain unknown. No account/provider registration or notification was sent. Document content may change after this check.

Evidence: [source QA](../quality/SOURCES-QA.md) and [source code review](../quality/SOURCES-CODE-REVIEW.md). Functional commit `8528567` (`feat(sources): retrieve bounded official documentation evidence`) accepted by the lead; push to origin/work succeeded and was observed by the lead. General live-source discovery, semantic/AI extraction, external adapters, monitoring, notifications and production operations remain incomplete.

## M4 verified integration — 2026-11-06

AUTH-01b production settings guards implemented and accepted for the local scope by independent QA/code review. Explicit exact hosts/origins, absolute data path and Secure cookie are required; production plaintext routes are denied except health. Malformed authorities, duplicate/empty Origin and forged forwarding headers are tested. Shipped Docker CMD uses --no-proxy-headers; real trusted HTTPS termination is not verified.

Root full suite:65/65 passed,7.366s. Both Chromium regressions passed with no JS errors. Separate container build with TLS verification and temporary CA mount succeeded; rebuilt non-root image passed65/65 tests,8.695s, and real HTTP health/root/static200. Initial COPY ownership failure was diagnosed and fixed. QA real Uvicorn production invocation showed internal HTTP health200, plaintext+spoofed-XFP signup400 and zero created users. See ../quality/DEPLOYMENT-QA.md, ../quality/DEPLOYMENT-CODE-REVIEW.md and OPERATIONS.md for actual boundaries.

M4 functional commit/push pending creation. No high defect remains in the reviewed local slice; production release still unaccepted. Remaining work includes verified identity/password recovery/abuse controls, general source ingestion and normalization, AI/semantic relevance, reviewed provider adapters, durable monitoring/notifications and real deployment/backup/rollback/load/security validation. Credentials/hosting are not the only gaps: these software capabilities remain unfinished.
