# Web/API Contract

Version 1, 2026-10-29. The first application exposes server-rendered HTML routes. This document distinguishes the agreed route surface from behavior that still requires implementation verification. It is not a promise of a public JSON API.

## Shared semantics

- Entrypoint: `app.main:create_app`; SQLite stores identity, goals, registrations and audit records.
- Authentication uses a server-validated session cookie. Private requests require a current session; ownership is derived from that session, never a client-supplied owner ID.
- Browser mutations require CSRF protection and use POST. A successful mutation redirects to the resulting page using Post/Redirect/Get.
- Untrusted values are escaped in HTML. Invalid fields produce a visible validation error without changing state. Error output never contains passwords or tokens.
- Private object IDs must be scoped in database queries. Unknown and inaccessible objects should not expose another user's records.

## Implemented route surface

Inspected in `app/main.py`; execution evidence is maintained by QA separately. Every POST requires `csrf` in the form body. Private POSTs also require a session.

| Method | Route | Form/query fields | Result |
| --- | --- | --- | --- |
| GET | `/register`, `/login` | None | HTML form with preauth CSRF cookie/token |
| POST | `/register`, `/login` | `email`, `password`, `csrf` | Session created; 303 to `/` |
| POST | `/logout` | `csrf` | Session invalidated; 303 to `/login` |
| GET | `/` | Optional `q` (up to 300 chars used) | Dashboard, keyword catalog search, goals, applications, notifications and recent audit; anonymous redirects to login |
| POST | `/goals` | `text` (3–300 chars), `csrf` | Persist goal; 303 to dashboard |
| POST | `/settings` | `country` (two letters), `student=on`, `automation=on`, `csrf` | Update profile and invalidate outstanding decisions; 303 to `/#profile` |
| POST | `/applications` | `opportunity_id`, `csrf` | Evaluate and create intent; 303 to `/#applications` |
| POST | `/applications/{id}/review` | `csrf` | Reevaluate owned intent; 303 to tracking section; this is not approval or remote submission |
| POST | `/applications/{id}/cancel` | `csrf` | Cancel owned tracking record; 303 to tracking section |
| POST | `/account/delete` | `confirmation=DELETE`, `csrf` | Delete user and dependent records; clear current cookie; 303 to `/register` |
| GET | `/healthz` | None | JSON `status=ok`, `mode=research-catalog`, `external_submission=false` after DB query |

Profile and tracking are dashboard sections; there are no separate GET `/settings`, `/applications` or `/opportunities` routes in this increment.

Validation uses 400, unauthenticated private mutations 401, invalid CSRF 403, missing/inaccessible objects 404, duplicates/invalid transitions 409, declared oversized bodies 413, and authentication throttling 429. The current throttle is process-local (10 attempts per source address per minute); it is not a distributed protection guarantee. Login passwords are 12–128 characters. Session duration is 12 hours; preauth token duration is 30 minutes.

Create-app test interface: `create_app(db_path=None)`. Default path is configured by `AOH_DB_PATH`; `AOH_SECURE_COOKIES=true` enables Secure cookies and must be configured for HTTPS deployment. Public production hardening is a release gate, not established by these route definitions.

## Domain contracts

### Policy result

Implemented interface: `evaluate(opportunity, profile, automation_enabled=False) -> (status, reason)` in `app/policy.py`. Current statuses are `blocked`, `needs_user_action` and `awaiting_approval`. There is deliberately no external executor and no current `allow` result.

Current checks include expiry, country restrictions, prohibited automation, student requirement, research-example provenance and unknown automation permission. `automation_enabled` is accepted but never authorizes execution in this increment. Awaiting approval is a tracking state, not a completed scoped-approval implementation.

The eventual deterministic contract in [SRS](SRS.md) adds current user permission scopes, fresh verified evidence, payload/destination/version binding and reviewed adapter availability. Those requirements must pass before any external action can become allowed.

### Registration intent

A registration intent identifies user + campaign/opportunity and stores policy decision, current state and relevant timestamps. Its creation does not submit a remote form. An `external_submitted` claim requires receipt or equivalent observable evidence from the executor.

Duplicate POSTs return HTTP 409 conflict without creating multiple independent registrations. A browser refresh after redirect must not submit again.

### Evidence

Display source URL, retrieved/checked timestamp, excerpt and verification state. A static catalog entry must state its provenance and cannot claim real-time verification. An evidence URL is a reference, not permission to fetch any arbitrary host or to send credentials.

### Audit

Persist actor ID, action, object ID, timestamp, decision/reason and relevant version. Logs are scoped to the authenticated user. Do not log session cookie values, plaintext credentials, unneeded profile fields or raw model reasoning.

## External integration contract

Provider connectors need explicit configuration, bounded timeouts/retries, schema validation and status reporting. An unavailable connector returns a visible unavailable/manual-handoff state. It must not fabricate results.

The first route surface does not claim Gmail OAuth, Discord delivery, LLM semantic search, live crawling, browser registration or webhook receipt ingestion. Each requires a separately tested connector and contract. External credentials are not necessary for local catalog-based development.

## Compatibility and evidence

Automated API tests should exercise real HTTP requests against a temporary database rather than mock away authentication/policy boundaries. A successful health response alone does not establish application readiness. Release reports must list routes/features actually tested and any differences from this target contract.
