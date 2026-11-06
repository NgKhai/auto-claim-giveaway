# AUTH-01b: deployment configuration guards

Date: 2026-11-06. Team decision under existing autonomous-development authorization. Goal: prevent accidental insecure runtime configuration before public deployment; this is not a claim that public authentication or deployment has been certified.

Use immutable reviewed settings instead of deriving production policy from arbitrary request Host headers. Existing stack and isolated workspace remain unchanged. Alternatives were relying entirely on a reverse proxy (leaves direct application exposure unsafe), or a larger hosted identity replacement (requires provider and operational setup). This local increment validates application configuration explicitly.

## Configuration

- HUNTER_ENV defaults development; only development and production are supported.
- Development accepts localhost, 127.0.0.1, ::1 and testserver hosts, preserving internal browser/API tests and dynamic local ports. No wildcard hosts.
- Production requires nonempty HUNTER_ALLOWED_HOSTS (comma-separated exact DNS names/IP hosts without scheme, port, paths or wildcards) and HUNTER_TRUSTED_ORIGINS (comma-separated exact HTTPS origins, optional valid port, no credentials, query, fragment or nonempty path). Each origin hostname must belong to the allowed hosts. Hostnames normalize lowercase. Empty list items are rejected.
- Production requires explicit absolute HUNTER_DB_PATH and HUNTER_SECURE_COOKIE=1. Missing or invalid configuration stops startup with a safe setting-name error, without printing secret/config values. Absolute path is a guard against accidental default storage, not proof that a persistent volume is attached.

## Request controls

Untrusted Host requests fail before data mutation. Production unsafe requests with an Origin must match the configured origin set regardless of the request Host. Cross-site Fetch Metadata is denied. Authenticated writes still require the session CSRF token. Same-origin enforcement in development remains compatible with local ports. Native clients without Origin remain supported; absence of Origin never bypasses authenticated-write CSRF. Login/signup remain unauthenticated entry points requiring later verification and abuse-hardening gates.

Production rejects non-HTTPS requests before routes, except /api/health for internal container readiness. The app does not interpret raw X-Forwarded-Proto as proof of HTTPS; trusted proxy middleware/server configuration must establish the ASGI scheme. Production session cookies must be Secure, HttpOnly and SameSite Strict. Production emits HSTS max-age=31536000; deploy only behind trusted HTTPS termination. Do not trust forwarded headers from arbitrary peers. No wildcard trust or blanket proxy-header acceptance is introduced.

## Acceptance

1. Invalid environment names, missing production settings, unsafe host patterns, malformed origins, mismatched origin/host, nonabsolute storage path or insecure-cookie settings fail startup.
2. Valid production configuration starts; allowed HTTPS origin can register/login and session cookies have the required flags and HSTS is present.
3. Untrusted Host or Origin cannot create an account or mutate owner data, including attempts to match a hostile Origin with a spoofed Host.
4. Existing ownership/CSRF/privacy/source controls and dev API/browser workflows continue passing.
5. Documentation provides configuration and deployment caveats; no real hosting, TLS provisioning, durable-volume, monitoring or production readiness claim without separate evidence.

## Plan

Backend tests first in tests/test_config.py, config module hunter/config.py and minimal app integration. Independent QA in tests/test_deployment_api.py and DEPLOYMENT-QA.md; independent review in DEPLOYMENT-CODE-REVIEW.md. Root runs full regression, both browsers, syntax/compile/diff checks, then creates a separate verified commit and pushes it. Preserve the M3 source increment and its tests. Hosted identity, password reset, email verification, distributed rate limits, retention, secrets, transitive dependency locks and operational drills remain later gates.

## Verified local outcome

Implemented in commit0230b95, pushed to origin/work. Root host regression65/65 and both Chromium flows passed. Rebuilt non-root container also passed65/65, with HTTP200 health/root/static runtime checks. Independent QA/code review is in ../quality/DEPLOYMENT-QA.md and ../quality/DEPLOYMENT-CODE-REVIEW.md. Container COPY ownership failure was fixed and retested; optional build CA mount preserves pip TLS verification. Production deployment, real TLS/proxy termination and full hosted authentication remain unverified.
