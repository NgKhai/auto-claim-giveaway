# Autonomous Opportunity Hunter — Product requirements

Status: implementation scope and release gates, 2026-11-05. This document supersedes the research documents' unchosen scope where it explicitly makes a product decision. It does not assert completed implementation, provider permission, or production readiness.

## Problem and audience

Developers and students seeking AI/developer resources need help finding legitimate benefits, understanding eligibility, submitting permitted applications and following up. Student status is optional and must never be inferred. The product should reduce time to a valid application while making evidence, uncertainty and authorization visible.

The full product supports free tiers, trials, credits, student benefits, giveaways, hackathons and grants. It must distinguish guaranteed credits from probabilistic prizes and disclose payment, renewal, region and deadline conditions. No promise of winning or universal registration coverage is permitted.

## Product decisions

- Begin with a complete local sandbox journey. All bundled opportunities and receipts must be visibly synthetic. Sandbox success is not provider approval or fulfillment.
- Use goal-led search, a minimal profile, evidence-backed explanations, deterministic authorization, explicit approval and persistent tracking.
- Use Python/FastAPI and a modular monolith; SQLite is the local development store. Hosted multi-user identity, database operations and external credentials are later release gates.
- Prefer provider-specific, reviewed adapters. An unsupported provider falls back to a source link and human handoff. General adaptive browser execution cannot invent or run new code.
- External integrations are optional capabilities with honest unavailable states, rather than fake successful results.

## Core journeys

1. Enter a goal and only the profile fields needed for eligibility.
2. Review relevant opportunities with source, evidence, last verification, eligibility, deadline and risk reasons.
3. See the data and destination of a proposed registration and its policy outcome.
4. Grant permission or approve that exact action; revoke before execution when necessary.
5. Execute an authorized action on a supported provider; handle CAPTCHA, authentication, sensitive fields and uncertainty through handoff.
6. Follow submitted, pending, rejected and confirmed results with receipts, deadlines and notifications.
7. Inspect activity, pause automation and exercise data deletion controls.

## First increment: local sandbox

A user searches the bundled catalog, evaluates a candidate, approves an exact sandbox registration and observes a durable receipt and audit trail. At least one candidate is permitted, one requires approval or more information, and one is blocked. The interface explains the difference. Input rejection and authorization failure must not produce a registration.

Required acceptance:

- Demo data is explicitly identified on the catalog and registration result.
- A goal produces understandable matching results; empty or invalid input has a useful error.
- Opportunity details expose evidence and known unknowns. Missing evidence cannot be represented as verified legitimacy.
- Expired, ineligible, payment/sensitive-data or automation-prohibited actions are denied; incomplete permission leads to approval/handoff.
- Approval identifies destination, action, exact data and version. Changing these invalidates that approval.
- Policy is checked immediately before execution, including revoked or expired permission.
- Repeated execution of the same sandbox application does not create duplicate receipts.
- Receipt and activity survive application restart; submitted does not imply approved or reward claimed.
- Relevant automated checks and independent QA review pass before this increment is marked Done.
- Account/session ownership and authenticated-write CSRF checks pass for the implemented web/API workflow; these local checks alone do not establish production security.

## Roadmap and release boundaries

| Milestone | User value | Exit gate |
| --- | --- | --- |
| M0: foundation and contracts | Reproducible local workflow and shared rules | Requirements, ADR, automated validation and startup instructions exist |
| M1: sandbox vertical journey | Goal → evidence → policy → approval → receipt → tracking | First-increment acceptance passes, independently reviewed; limitations visible |
| M2: identity and real read-only discovery | Secure personal workspace and current opportunities | Account isolation, source permission, SSRF defenses, evidence freshness and extraction evaluation verified |
| M3: bounded real registration | Supported providers with human takeover | Provider-specific permission evidence, browser tests, concurrency/recovery and revocation checks pass |
| M4: monitoring and notifications | Actionable follow-up over time | Scheduler restart, deadline timezone, deduplication and email/Discord failures verified |
| M5: production release | Reliable hosted service | Realistic critical E2E journeys, security acceptance, operational monitoring, backup restore and rollback verified |

Do not market M1 as production-ready. M2–M5 are required work, not silently dropped scope. A hosting or credential blocker must identify the exact unverified capability.

## Quality and success criteria

Measure relevance on labeled goals, factual extraction against reviewed evidence, eligibility false positives, unauthorized action count, duplicate submissions, task completion, handoff rate, latency and cost per valid application. Establish real baselines before setting performance claims. No fabricated coverage percentages or benchmark outcomes.

Release requires zero unresolved critical/high defects, traceable acceptance coverage, passing CI, successful deployment/rollback and restore drills, operating health/error monitoring and PM/QA sign-off. Every result report must distinguish tested, failed, skipped and unavailable integrations.

## Non-goals and prohibited behavior

No CAPTCHA bypass, rate-limit evasion, bulk account creation, automatic financial/credential/document submission or unsupported provider automation. No provider request occurs merely because a user approved it when provider rules forbid automation. No LLM confidence score can grant permission. No notification is sent without configured destination and authorization.
