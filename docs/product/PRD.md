# Product Requirements — Autonomous Opportunity Hunter

Status: implementation baseline, 2026-10-29. Owner: PM. This document incorporates the user's autonomous-development directive; the earlier research remains evidence and alternatives, not a claim that integrations have been validated.

## Product outcome

Help a user turn a goal into relevant opportunities, informed registration decisions and follow-up actions. A successful journey makes the source, eligibility, permission decision and actual registration state understandable. A submitted application is never presented as a reward received.

Initial audience: developers and students seeking AI resources and developer benefits. Student status is explicit profile information, not an assumption. The product model also supports trials, giveaways and hackathons without treating uncertain prizes as guaranteed credits.

## Scope and operating decisions

Build a modular Python/FastAPI application with server-rendered pages and SQLite for the first single-instance deployment. Provider adapters and policy are separate from presentation. This is a bounded initial operating model, not a promise of horizontal scalability. The architecture owner records detailed trade-offs in an ADR.

The first complete increment is: user creates a goal, views source-backed opportunities, requests an application, sees a deterministic decision, gives any permitted approval, and tracks the resulting status and audit history. Unsupported live registration produces a clear manual-action state; it must not fabricate an external receipt. Fixtures are labeled as fixtures and are not evidence of live discovery.

## Product requirements and acceptance

| ID | User need | Product acceptance criterion |
| --- | --- | --- |
| PR-01 | Maintain a profile and preferences | User can save relevant country and eligibility attributes, change them, and see missing information; another user cannot read or modify them. |
| PR-02 | Describe a goal | A valid natural-language goal persists and can be revisited; empty/oversized input produces an actionable validation error. |
| PR-03 | Discover relevant opportunities | Results show why they match, their category and source; empty, unavailable and failed discovery are distinct states. Keyword fallback is labeled and never described as model-based semantic matching. |
| PR-04 | Understand evidence | Opportunity details include source URL, retrieval time and evidence for important conditions. Missing, contradictory or stale facts remain visible. |
| PR-05 | Check eligibility | Expired or incompatible opportunities cannot be auto-submitted; missing profile requirements produce uncertainty or manual follow-up. |
| PR-06 | Control automation | Permissions specify allowed provider/action/data and can be revoked. Decision is evaluated again before execution; LLM confidence cannot grant permissions. |
| PR-07 | Approve a concrete action | Approval shows destination and exact fields to disclose, applies to a specific action version, and cannot override prohibited behavior. Changed payload requires a new decision. |
| PR-08 | Register reliably | Only reviewed adapters for permitted providers can submit. CAPTCHA/authentication/unsupported forms require takeover. Unknown submission outcome does not trigger a blind retry. |
| PR-09 | Track applications | User sees persisted status, timestamps, next action and receipt when available; repeated clicks do not create duplicate applications. |
| PR-10 | Receive follow-up | In-app notifications persist and can be marked read. Email/Discord delivery requires configured credentials and records failures without losing application state. |
| PR-11 | Inspect and control data | User can inspect activity, stop automation and use documented export/deletion controls; secrets and sensitive form data are excluded from logs. |
| PR-12 | Use an operable service | Setup, health checks, migrations, backup/restore and rollback have executable instructions and measured validation outcomes. |

## Experience principles

Each screen provides one clear next action and uses explicit states: checking, needs information, awaiting your approval, blocked, requires manual registration, submitted, and outcome unknown. Show why an opportunity was rejected without describing uncertainty as fraud. Keep reward availability separate from application approval.

Approval is about the actual action, not a blanket acceptance of a model's plan. A user can withdraw permission before execution. An already completed external action cannot be undone by changing its local status.

## Capability coverage required for the eventual release

The full requested product includes semantic matching, extraction, source verification, eligibility, scoped permissions, human approval, browser automation, bounded adaptation to changed forms, monitoring, email/Discord, audit and privacy. An initial increment may deliver a subset, but the roadmap must retain outstanding capabilities. No feature becomes complete solely because a mocked integration passed.

## Product exclusions

Never bypass CAPTCHA, authentication or provider restrictions. Never automatically submit financial details, passwords or sensitive credentials. Do not create arbitrary executable code from website instructions. These are explicit constraints from the user's request, not optional future hardening.

## Success measures

Measure relevant opportunities per goal, evidence completeness, eligibility false positives, unauthorized-action count, duplicate submission count, confirmed submission rate, time to useful next action and provider/model cost. Establish a baseline before publishing target percentages; no invented success rate or performance SLA.

## External prerequisites and release gates

Live LLM evaluation requires a working model credential. Real browser registration requires a provider whose terms permit automation and a suitable test account. Notification delivery requires authorized channel credentials. Public release requires hosting, domain/TLS, authentication and operational ownership. Their absence does not block local development, but blocks corresponding live acceptance claims.

A production release requires all critical journeys tested in realistic conditions, independent QA and PM acceptance, no unresolved high/critical defects, verified CI, deployment/rollback/restore and operational monitoring. Until those gates have recorded evidence, label the release as development/preview.
