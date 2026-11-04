# Software requirements specification

Status: normative target requirements, 2026-11-05. Implementation/test reports determine which requirements are delivered. Exact endpoint spelling and storage schema belong in the implementation's API contract; the requirements below do not assert that APIs already exist.

## Actors and trust boundaries

The account owner supplies goals, profile and scoped consent. Discovery sources and browser content are untrusted. The orchestrator proposes structured facts/actions; verifier attaches evidence; deterministic policy authorizes; reviewed adapters execute; tracker reconciles; notifier delivers configured messages. Text from sources must never grant access to tools, secrets, other accounts or arbitrary code execution.

The local sandbox release is a development workflow. Internet-facing multi-user use requires verified identity, authenticated sessions, account ownership checks, CSRF protection where applicable, rate limiting and tenant isolation. A local single-user shortcut cannot be presented as production authentication.

## Functional requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| FR-01 | Validate and persist a bounded nonempty goal; support keyword/product/natural-language input | Valid goal accepted; blank, oversized and malformed requests rejected without state corruption |
| FR-02 | Match opportunities and expose matching reasons | Relevant bundled fixture found; unmatched query has an honest empty result |
| FR-03 | Normalize type, reward conditions, countries, eligibility, deadline, payment/renewal and source facts | Facts retain evidence references; unknown facts remain unknown |
| FR-04 | Distinguish synthetic fixtures, snapshots and live verified data | Visible origin and verification time; demo result never says real provider fulfillment |
| FR-05 | Evaluate deterministic policy with structured reason codes | Expiry, country, missing facts, forbidden data and automation permission cases covered |
| FR-06 | Bind approval to owner, opportunity/provider, destination, action, exact payload fingerprint, adapter/form version and expiry | Mutation, cross-owner access, expiry and revocation prevent execution |
| FR-07 | Re-evaluate policy at execution time | Permission revoked after approval prevents side effects |
| FR-08 | Execute only reviewed adapters and authorized field sets | Unknown adapter/domain or extra fields fail closed; sandbox is the only M1 executor |
| FR-09 | Prevent duplicate local execution; persist attempt before external side effects | Repeated/concurrent requests produce one local registration; ambiguous external outcome cannot automatically retry |
| FR-10 | Persist receipt, application state and structured activity | Restart preserves state; timeline explains decision and execution result |
| FR-11 | Handoff unsupported/CAPTCHA/authentication/OTP/sensitive-data cases | No bypass or unattended sensitive submission; actionable reason displayed |
| FR-12 | Reconcile submissions separately from provider review and benefit fulfillment | A submission receipt never implies award approval or claimed benefit |
| FR-13 | Monitor deadlines with timezone and bounded scheduling | Restart, expired deadlines, duplicate jobs and provider outages tested |
| FR-14 | Deliver authorized in-app/email/Discord notifications with deduplication | Retries bounded; unavailable destinations clearly reported; no false sent state |
| FR-15 | Support profile minimization, automation pause/revocation and deletion | Revocation checked before execution; deletion and retention policy verified |

FR-01–10 form the first vertical slice, subject to implementation coverage; FR-11 initially requires safe rejection/handoff rather than external browser integration. FR-12–15 remain target release requirements and must not be marked implemented from documentation alone.

## Policy decision order

1. Verify caller ownership and request structure.
2. Deny expired/ineligible opportunities, forbidden actions or fields, payment/credential submission, unpermitted automation and unsupported destination/adapter.
3. Route missing evidence, unknown eligibility, authentication challenges and incomplete facts to human review/handoff; approval alone cannot override prohibition.
4. Require active scoped authorization, or approval of the exact current payload/version when allowed by policy.
5. Recheck all mutable rules immediately before side effects and record the resulting decision.

`allow`, `requires_approval`/`needs_user_action` and `deny` are distinct outcomes. Human approval cannot transform unknown provider rules into affirmative automation permission. Low risk is necessary but insufficient for automatic registration.

## Logical data contract

| Entity | Minimum meaningful data |
| --- | --- |
| Goal | ID, owner, bounded text, creation time |
| Profile | Owner and explicitly supplied eligibility fields; no inferred student status |
| Opportunity | ID, source kind, title, type, source/destination, conditions, deadline/timezone, countries, adapter/form version |
| Evidence | ID, source, observed time, supported fact/excerpt, verification/contradiction status; fixture marker |
| Permission | Owner, purpose, destination, action, allowed fields, validity, policy version, revocation |
| Approval | Owner/action binding, immutable payload fingerprint, version, validity and decision |
| Application | Owner/opportunity, idempotency key, attempt/state, payload reference, receipt, reconciliation state |
| Activity | Owner, event/time, actor, decision/reason, evidence/action references; no raw secrets or model chain of thought |
| Notification | Owner, event, channel/destination reference, idempotency key and delivery outcome |

Use explicit timestamps with timezone. Fingerprints must use a canonical representation; a client-supplied fingerprint is not trusted proof. Foreign-key ownership checks apply across all references.

## State and recovery

Conceptual lifecycle: `draft → awaiting_approval → ready → submitting → submitted → pending_review → approved/rejected`. Additional states include `needs_user_action`, `submission_unknown`, `expired`, `failed`, `cancelled`. The first increment may expose a smaller explicit subset; document that subset in its API contract.

Approval and provider acceptance are separate records. Fulfillment is separate again. An external timeout after possible submission becomes `submission_unknown`; reconcile using provider evidence before retrying. A database unique key prevents duplicate local work but does not prove exactly-once delivery to an external website. Restart may resume review, but must not blindly resubmit an uncertain attempt.

## Security and operational requirements

- Validate input size/type and ownership server-side; use parameterized database operations, escaped output and restrictive content handling.
- No arbitrary URL fetching from goals or source text. Before live discovery, validate scheme/host, reject private/loopback/link-local/reserved targets and revalidate redirects and DNS resolution; browser sessions require equivalent egress isolation.
- Keep secrets outside Git and logs. Proxy placeholders cannot be assumed usable as local passwords. Minimize submitted PII and redact audit/trace output.
- Bound request size, retries, execution time and browser resource use. Retry only operations whose outcome permits retry.
- Database migrations, configuration validation, health/readiness, structured errors, backup/restore and rollback need reproducible documented commands.
- SQLite is a local development decision. Production storage/concurrency must be chosen and validated before hosted release.

## Required test matrix

Test the successful first journey through HTTP/UI and persistence, then negative paths: empty/oversized goal, unmatched search, expiry boundary, country mismatch, missing evidence, forbidden fields, altered payload/version, revoked/expired approval, duplicate/concurrent execution, restart, cross-owner references and untrusted HTML/content. Later browser tests cover DOM drift, redirects, CAPTCHA and uncertain submission. Later notification tests cover outages, retries and deduplication. Load tests must use measured thresholds; no production scale claim follows from a local health request.
