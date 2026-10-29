# Independent QA report — initial research workspace

Reviewed 2026-10-30 (Asia/Bangkok). Reviewer: independent QA agent; production implementation by separate Dev agent. Working branch: `feat/opportunity-platform`; root records commit/push separately.

## Scope and verdict

The authenticated **local research and manual tracking slice** passes the checks below. This is not acceptance of the full Autonomous Opportunity Hunter product and is not a production-ready release. No provider registration, AI model call, live opportunity fetch or outbound notification occurred.

## Executed evidence

- `.venv/bin/python -m pytest -q`: **28 passed**, one Starlette/AnyIO deprecation warning, 1.50 seconds on the final QA run.
- `python3 tests/browser_smoke.py`: **passed** using actual `/usr/bin/chromium`, an isolated temporary SQLite database and a locally started Uvicorn server. Browser and server were stopped after the test.
- `git diff --check`: passed.
- Tests require sandbox escalation in this environment because default socket/thread/browser restrictions can hang TestClient or prevent Chromium startup. No external destination is contacted by the browser test.

## What was exercised

Authentication and session replay after logout; server-side CSRF rejection; cross-user visibility and mutation denial; password/session hash storage; goal validation and HTML escaping; security response headers; sequential and four-worker concurrent duplicate intent prevention; profile/permission invalidation; cancellation; persistence across app recreation; account deletion cascades; malformed, timezone-unknown and expired deadlines.

Real browser journey: create account → save goal → search cloud leads → track lead → recheck eligibility → cancel → mobile viewport overflow check → sign out → sign in → observe persisted goal and cancelled tracking. No JavaScript page errors were observed. This checks mobile horizontal overflow, not a complete accessibility audit or visual review across devices.

## Defects reproduced and retested

| Finding | Initial evidence | Fix/retest |
| --- | --- | --- |
| Date-only deadline raised TypeError | Independent policy test failed comparing naive/aware datetime | Fail-closed user-action result; suite passed |
| Malformed deadline raised ValueError | Independent policy test failed on invalid ISO string | Fail-closed user-action result; suite passed |
| `AOH_SECURE_COOKIES=1` did not set Secure | Dev regression test reproduced during independent baseline run | Configuration accepts 1; suite passed |
| Browser error recovery returned raw JSON | Dev regression test reproduced during independent baseline run | HTML error page for browser Accept header; suite passed |

Initial run while Dev tests were landing: **24 passed, 4 failed**. Final run: **28 passed**. Failures were fixed in implementation; independent assertions were not weakened.

## Remaining release gaps

- Research catalog has three static leads, not verified live offers; relevance is keyword overlap, not semantic matching.
- There is no external submission adapter, payload-bound approval or receipt reconciliation. `review` only re-evaluates a local tracking intent.
- Source freshness, full permission scopes, unknown/contradictory evidence, prompt-injection isolation and real provider terms need implemented contracts and tests before autonomous actions.
- In-app notifications are local status records; durable monitoring and external email/Discord delivery remain unverified/unimplemented.
- In-memory authentication throttling is not a shared durable abuse-control system; password recovery, email verification and broader auth hardening remain release work.
- Resource limits need streaming/chunked-body validation beyond the current Content-Length gate.
- Realistic load, complete accessibility coverage, remote CI, container deployment, backup/restore/rollback and operational alerts are separate release gates.
- No general assertion is made that untested code paths are defect-free. Product acceptance and overall release approval remain pending.

## Container finding from integration review

Root reported a container runtime `PermissionError` reading `/app/app/__init__.py`: copied host files had restrictive permissions and root ownership while the container runs as `app`. Root changed the Dockerfile to `COPY --chown=app:app`; runtime retest is owned by root and must be recorded before declaring the artifact verified. This finding was not discovered by the QA browser test.
