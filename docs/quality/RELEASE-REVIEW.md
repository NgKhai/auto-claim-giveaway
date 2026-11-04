# Independent quality review — initial sandbox increment

Reviewed 2026-11-05 by the QA workstream independently of implementation.

## Decision

Accept the initial local sandbox workflow on the evidence below. Reject any claim of production readiness or complete fulfillment of the full product request. Production capability gaps listed below remain release blockers.

## Evidence executed

- `python3 -m unittest discover -s tests -v`: **22 tests passed** in the final integrated run (14 independent API acceptance tests plus 8 developer workflow tests), 2.276 seconds.
- `python3 docs/quality/browser_smoke.py`: **passed**, rerun after TTL/destination/Origin protections and expired/revoked approval renewal. A subsequent browser run after frontend confirmation explicitly passed consent action `sandbox.register`, destination `sandbox://opportunity-hunter/credits`, adapter-version label, 15-minute expiry disclosure, and audit display year matched to persisted Unix-second timestamps. Uses a real headless system Chromium instance, a temporary SQLite database and its own localhost server. Covers account signup, goal discovery, exact payload approval dialog, sandbox submission receipt, page reload/persistent application state, 390px mobile width without horizontal overflow, and logout. No browser JavaScript errors observed.
- API negative checks cover unauthenticated access; invalid CSRF; cross-account submit/revoke/approve and audit isolation; unknown opportunity; client-supplied sensitive payload; wrong credentials; expired approval; changed persisted payload; changed destination descriptor; provider-policy expiry after approval; and unmatched query returning no results.
- Four concurrent submit requests return one identical receipt and generate exactly one `sandbox_submitted` audit event. This demonstrates local SQLite serialization, not external exactly-once delivery.
- A new app instance using the same database preserves the application and receipt and reuses that receipt on repeated submit.

Commands required the managed executor's supported elevated execution mode for local sockets. Restricted execution's TestClient hang/Chromium launch failure is an execution restriction; it does not establish an application or Git proxy outage.

The browser smoke script is optional: install Playwright separately (`python -m pip install playwright`) and provide system Chromium at `/usr/bin/chromium`. Playwright is not included in the application requirements. Current CI runs the API suite; the browser smoke was executed in this managed session and is not currently a CI browser gate.

An earlier wording claimed final frontend display fixes had been rerun before checking their presence. That statement was corrected to pending; the explicit assertions above were then executed against the saved frontend changes.

## Review findings resolved

1. Initial opportunity matching returned all fixtures for unmatched goals. Backend now filters positive relevance, with independent regression coverage.
2. Initial approval lacked expiry. Backend now persists a 15-minute expiry and rejects expired execution, with independent regression coverage.
3. Approval binding now includes destination/action/adapter and required field descriptor alongside opportunity, payload and version. Changed destination is independently tested.
4. Cross-origin authentication mutations are denied in middleware, preventing login-CSRF; authenticated mutations also require the session CSRF token.

## Important limitations and outstanding release gates

- All opportunities are explicit synthetic fixtures. There is no verified real-provider discovery, extraction, semantic search/LLM workflow or actual reward.
- Submission creates a local sandbox receipt only. No external form/browser adapter or provider authorization has been validated. CAPTCHA/OTP/DOM drift and ambiguous external submission recovery are unrun and remain unavailable.
- Continuous monitoring, real email/Discord notification delivery, profile deletion/retention and general scoped automation permissions remain incomplete.
- Browser smoke exercises one happy path and one mobile size, not accessibility certification or a cross-browser/device suite.
- Security review is focused local code/API review, not penetration testing. Internet-facing auth verification, distributed abuse controls, body-size limits, operational account lifecycle and production hosting hardening remain separate gates.
- No realistic load/performance benchmark, production deploy, production migration/rollback, backup restore, or monitoring alert delivery was verified in this QA pass.
- SQLite approval/concurrency evidence applies to this local executor only; scaling and external side-effect transactions require separate validation.

The server rechecks ownership, approval fingerprint/expiry and deterministic opportunity policy before local execution. No arbitrary URL fetch, LLM-generated code execution, external registration or notification send occurs in the tested sandbox path.
