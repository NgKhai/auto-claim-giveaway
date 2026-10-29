# Software Requirements Specification

Status: normative requirements, not a statement that every feature is implemented. Version 1, 2026-10-29. Read with [PRD](PRD.md), [roadmap](ROADMAP.md) and [API contract](API.md).

## System boundary

The initial delivery is a single-instance FastAPI application with SQLite persistence and server-rendered pages. Users manage their own goals and registrations. Catalog evidence is distinguished from live verification. The first complete journey ends in a tracked registration intent or manual handoff; it must never report external submission without an external receipt.

Subsequent milestones add permitted source ingestion, semantic matching, reviewed registration adapters, durable monitoring and notification providers. SQLite is a single-instance deployment decision, not a claim of multi-region durability.

## Functional requirements and acceptance

| ID | Requirement | Observable acceptance |
| --- | --- | --- |
| FR-01 | Identity and isolation | Unauthenticated requests cannot read private data; user A cannot read/change user B's goals, profile, approvals or registrations by substituting IDs. Passwords are hashed; logout invalidates the current session. |
| FR-02 | Profile and goals | A user can persist a bounded natural-language goal and country/student profile, edit it and see it after restart. Missing eligibility information remains unknown. |
| FR-03 | Discovery and relevance | Results match the supplied goal using a documented matching mode. Empty and irrelevant searches produce an honest empty state. Curated catalog results are labeled; keyword matching is not described as semantic AI discovery. |
| FR-04 | Evidence and normalization | Opportunity type, source URL, evidence text, verification status and checked time are available. Deadlines carry timezone or remain unknown. Missing/conflicting evidence cannot become verified by model confidence alone. |
| FR-05 | Eligibility | Country, expiry and student restrictions are evaluated separately. Explicit incompatibility blocks automation; missing information requires user action. Evidence-backed eligibility does not imply a reward is guaranteed. |
| FR-06 | Deterministic policy | Server code returns allow, approval_required or blocked with reason codes. Allow requires current permission, verified/fresh evidence, known eligibility, permitted provider automation, reviewed adapter and authorized fields. Financial/credential submission and prohibited automation are blocked. |
| FR-07 | Approval and revocation | Approval is scoped to user, opportunity/version, destination, action and payload. A second user cannot approve it. Revocation takes effect before execution; expired or changed evidence/payload invalidates approval. Approval cannot override provider prohibition. |
| FR-08 | Execution and handoff | Unsupported adapters, CAPTCHA, OTP and provider login trigger a clear handoff. The executor never runs arbitrary agent-written code. A live submit records receipt evidence; absent receipt remains unknown, not submitted. |
| FR-09 | Tracking and idempotency | One user/campaign registration intent is retained under duplicate requests. Attempt, submitted, pending_review, accepted and fulfilled remain distinct. Timeout after external submit does not blindly retry. Cancel/pause remain available before irreversible work. |
| FR-10 | Notifications | Users can view pending actions and deadlines in-app. Email/Discord are opt-in provider integrations with bounded retry and delivery state; unavailable providers cannot be shown as delivered. |
| FR-11 | Audit | State-changing actions persist actor, time, object, decision/reason and evidence/version references. Audit excludes passwords, session tokens and unnecessary PII. User-facing explanations do not require storing model chain-of-thought. |
| FR-12 | Privacy | User can inspect retained personal information and request/export/delete it through a documented path. Session/credential artifacts are protected and excluded from source control. Retention and backup deletion limits are disclosed. |

## Deterministic decision ordering

1. Validate identity, object ownership and request shape.
2. Block prohibited provider automation, prohibited data types, explicit ineligibility or expired opportunities.
3. Require handoff/approval for unknown evidence, unknown provider permission, missing profile facts or unsupported adapter; explicit human approval does not resolve missing provider permission.
4. Require matching current user authorization and unchanged evidence/payload before allow.
5. Reevaluate immediately before any external side effect, including after approval or queued execution.

UI labels must distinguish policy permission from executor availability. A policy `allow` does not mean a submission happened. First delivery may implement a narrower set of states, but unsupported transitions must be rejected and the remaining requirements listed as incomplete.

## Workflow

Create account/session → save goal/profile → discover candidates → inspect evidence and eligibility → request registration intent → evaluate policy → block, request approval or hand off → track status and audit.

Live execution extends this with ready → submitting → submitted → pending_review → accepted/rejected. A transport failure during submit becomes submission_unknown until reconciled. Fulfillment is a separate result from acceptance.

## Security and reliability requirements

- Bound request bodies, text fields, external response size, retries and execution duration.
- Protect state-changing browser requests against CSRF; escape untrusted content in templates; parameterize database queries.
- Use secure, HttpOnly, SameSite cookies in HTTPS production; fail closed on insecure production configuration.
- Password hashing must use a standard salted password KDF; login must have abuse controls before public exposure.
- Browser/extraction tools treat page instructions as data; no arbitrary fetch URL may reach internal/private/metadata destinations, including redirect hops.
- Database changes are transactional; migrations versioned; duplicates handled at the database boundary.
- Restart preserves application records. Backup restore, migration rollback and deployment health must be tested before release readiness.
- Secrets come from secure configuration; never committed or exposed in responses/logs.

## Traceability and release evidence

Tests should identify the FR IDs they cover. Automated checks must include ownership tampering, unauthenticated mutation, expired/country/student restrictions, unsupported automation, approval escalation, duplicate requests, persistence after restart, malicious HTML, invalid inputs and service failures.

A green unit suite establishes only the behaviors it executes. Live sources, model calls, email/Discord delivery, real provider registration, production deploy/restore and load claims require their own observed evidence. Refer to the roadmap for tasks not yet delivered.
