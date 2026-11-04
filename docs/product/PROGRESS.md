# Shared delivery progress

Updated 2026-11-05. Full product remains incomplete and is not production-ready.

## Current milestone

M1 local sandbox journey implemented and accepted by independent QA for its tested scope. PM/BA's two conditional UI findings (exact-action consent and Unix audit time rendering) are resolved and explicitly verified in Chromium. Existing research files remain unchanged.

| Workstream | State | Evidence |
| --- | --- | --- |
| PM/BA | Local slice reviewed; full target preserved | PRD.md, SRS.md, BACKLOG.md |
| Backend | Verified local slice | 22 regression tests, ownership/CSRF/policy/consent/persistence/concurrency |
| Frontend | Verified browser journey | Real Chromium signup → goal → exact consent → sandbox receipt → reload → mobile → logout |
| Independent QA | Local slice accepted; production rejected | ../quality/RELEASE-REVIEW.md |
| Independent code review | See reviewer verdict | ../quality/CODE-REVIEW.md |
| Integration | Commit and push pending final record below | CI configured; remote CI not yet observed |

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

M1 functional commit: pending final creation. Target: origin/work; no merge to main. Update following actual Git result.

## Next prioritized tasks

1. AUTH-01: account lifecycle/privacy (export/deletion/retention), Internet-facing auth hardening and abuse controls; add acceptance and independent security tests.
2. SRC-01: permitted live read-only source registry, bounded ingestion, freshness/conflict evidence and SSRF/redirect/DNS controls.
3. AI-01: structured intent/extraction and semantic relevance with labeled evaluations, credential configuration and honest unavailable fallback.
4. WEB-01/REC-01: reviewed provider adapters and explicit authorization, browser handoff, uncertain-outcome reconciliation and durable workers.
5. MON-01/NOT-01: scheduling, pause controls, deduplication and authorized email/Discord notifications.
6. OPS-01/SEC-01/REL-02: production storage/migrations, locked dependencies, container build, real deployment/CI, measured load, monitoring, backup restoration and rollback validation.

Live-provider permission, AI credentials, authorized notification destinations and hosting are not configured or verified. They block live integration/release checks, not the local development workflow. No emails, real registrations, awards or external deployment are claimed. Remaining software work is explicitly unfinished, not mislabeled as solely credential-blocked. Continue with AUTH-01, using the saved backlog and this record rather than rebuilding M1.
