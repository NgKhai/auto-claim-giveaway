# Initial sandbox release test plan

This plan validates a local development increment, not production acceptance.

| ID | Scenario | Expected behavior |
|---|---|---|
| AUTH-1 | Unauthenticated private API | Denied without leaking account data |
| AUTH-2 | Create account, login, logout | Credentials hashed; session invalidated on logout |
| AUTH-3 | Cross-account application access | Denied, including approve/revoke/execute |
| CSRF-1 | Missing/incorrect CSRF token on authenticated writes | Denied |
| GOAL-1 | Create goal and discover opportunities | Goal persists; fixtures explicitly labeled sandbox |
| POLICY-1 | Expired deadline or incompatible country | Deterministic deny |
| POLICY-2 | Missing evidence, unknown requirements | No autonomous execution |
| POLICY-3 | Sensitive credential or payment field | Denied |
| APPROVAL-1 | Execute without approval | Denied |
| APPROVAL-2 | Approve exact payload then execute | Sandbox receipt and persistent tracked status |
| APPROVAL-3 | Payload/version changes after approval | Old approval unusable |
| APPROVAL-4 | Expired or revoked approval | Execution denied |
| EXEC-1 | Repeated submit | Same receipt; no duplicate registration |
| EXEC-2 | New app instance against same database | Application/audit persistence |
| AUDIT-1 | Approval, revoke, execute | Owner-visible structured audit without passwords/session tokens |
| UI-1 | Browser user journey | Not accepted without real browser execution |

## Release gates still beyond this increment

Real-source discovery/extraction, semantic and LLM integration, browser adapters, provider permissions, notification providers, continuous monitoring, production deployment, backup restoration and load/security validation require separately demonstrated evidence. Seed fixtures do not satisfy real-source verification. A local sandbox registration is not a provider registration or granted reward.
