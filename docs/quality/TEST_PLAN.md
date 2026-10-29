# Independent quality plan

Date: 2026-10-29. Scope: first authenticated vertical slice. This document is a plan, not a claim that tests have passed.

## Acceptance matrix

| ID | Requirement | Independent check | Release gate |
| --- | --- | --- | --- |
| QA-01 | Authentication protects personal information | Anonymous access cannot view/mutate goals, applications, audit, profile | Blocking |
| QA-02 | Tenant isolation | User B cannot read/change User A's goal/application by guessing identifiers | Blocking |
| QA-03 | CSRF protection | Missing/wrong tokens and cross-origin mutation requests fail without writes | Blocking |
| QA-04 | Safe password/session storage | Password plaintext absent; logout invalidates old session; secure cookie configuration | Blocking |
| QA-05 | Deterministic permission enforcement | Expired/prohibited/unauthorized input cannot reach submission through UI or direct API | Blocking |
| QA-06 | Approval is bounded | Changed/revoked permission invalidates queued action; approval cannot override prohibited provider action | Blocking |
| QA-07 | Duplicate prevention | Repeated/concurrent application requests yield one business application | Blocking |
| QA-08 | Honest registration status | No external submission is recorded without receipt evidence from a real configured executor | Blocking |
| QA-09 | Evidence and untrusted content | Evidence remains visible; goal/source markup is escaped, cannot execute scripts | Blocking |
| QA-10 | Recoverable persistent state | Reopening app with same DB retains tenant-owned goals/application/audit | Blocking |
| QA-11 | Input errors | Invalid/oversized goals and invalid IDs yield controlled responses without state corruption | Blocking |
| QA-12 | Browser journey | Signup → goal → opportunity evidence → application/approval → tracking → logout works in browser | Required before UI readiness |
| QA-13 | Basic performance | Small reproducible authenticated request loop reports latency/errors; no unsupported SLA claims | Baseline only |
| QA-14 | External integrations | Provider auth, browser takeover, notifications, failure recovery verified against actual configured services | Required for corresponding release capability |

## Execution method

Independent reviewer reads requirements and implementation, then adds tests in `tests/test_security_review.py` without modifying implementation. Bugs are reported to Dev with reproduction and expected/actual behavior. Dev fixes application code. Reviewer reruns tests and the affected regression suite. Fixtures use isolated temporary databases and synthetic identities only.

## Production release checks beyond this increment

- Real discovery/extraction and eligibility quality measured against labeled sources.
- Real provider-specific browser submission adapter with explicit automation permission and confirmation receipts.
- Restart/retry reconciliation, concurrency and unknown-result handling under actual workers.
- Model credentials, prompt-injection handling, semantic relevance and evidence verification.
- Notification delivery/retries and opt-out with authorized email/Discord integrations.
- Deployment TLS, secrets, migrations, monitoring, backup restoration and rollback exercised.
- Independent security review, CI pass on remote runner and product release acceptance.

Unavailable integration or infrastructure evidence remains an explicit release blocker; passing local tests does not close it.
