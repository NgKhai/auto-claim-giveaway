# Independent QA — AUTH-01b deployment configuration guards

Decision: accept the tested application configuration/request-boundary increment. This is not production release acceptance, a hosted deployment, or verified public authentication.

## Executed evidence

`python3 -m unittest discover -s tests -p test_deployment_api.py -v` completed with **11/11 passing**, 0.430 seconds after strict authority/empty-Origin/type validation fixes. The initial pre-implementation run failed importing the absent `hunter.config` module; that established a missing prerequisite, not behavioral or deployment success.

The independent acceptance tests exercise:

- Rejected environment names; missing production configuration; relative database paths; insecure-cookie values; wildcard, URL, path, credentials, port and empty-list host entries; insecure/mismatched/credential-bearing/path/query/fragment/invalid-port origin entries.
- Immutable settings and revalidation of direct dataclass replacements for insecure production fields.
- Configuration errors omit an injected secret-bearing configuration value.
- Untrusted Host and matching forged Host/Origin fail before account creation; database user count remains zero.
- An allowed Host does not authorize an unconfigured, HTTP, suffix-spoofed, opaque, empty or duplicate Origin; malformed Host authority syntax is rejected. No account mutation follows.
- Allowed HTTPS origin registration works with Secure, HttpOnly, SameSite Strict session cookie and HSTS. Authenticated CSRF-protected goal mutation succeeds.
- Native requests without Origin remain usable over HTTPS, but authenticated writes still require the CSRF token.
- Production HTTP account creation is denied, including a raw `X-Forwarded-Proto: https` header; no user is inserted. The HTTP health-check exception works, while the normal root path remains denied.
- Development preserves the four local/test hosts and omits production HSTS.

The production API tests use HTTPS ASGI scopes through TestClient, not a TLS certificate or an actual trusted reverse proxy.

A separate real-runtime subprocess check launched `python -m uvicorn hunter.app:app --host 127.0.0.1 --port <temporary-port> --no-proxy-headers` with valid synthetic production settings, an explicit temporary database and Secure cookies. Actual HTTP requests observed health **200**, plain registration **400**, registration with `X-Forwarded-Proto: https` also **400**, and database user count **zero**. The process was terminated and temporary files removed. This verifies the documented forwarding-disabled invocation locally; real reverse-proxy/TLS termination remains unverified. Existing functional/source API tests and both browser scripts are separate integration checks; their latest execution totals belong in the root integration record.

## Review limits and operational gates

Uvicorn/reverse-proxy configuration must not accept forwarded-protocol claims from arbitrary peers. TestClient proves the application itself does not interpret a raw forwarding header; it cannot prove an upstream server has not rewritten the ASGI scheme. Production launch must disable automatic proxy-header trust or explicitly constrain reviewed trusted termination peers. The local forwarding-disabled invocation was separately checked above; enabling trusted proxy rewriting still needs a reviewed deployment-specific configuration.

An explicit absolute database path is not evidence of durable storage, backup/restore, migration rollback or volume attachment. Secure-cookie/HSTS behavior does not establish HTTPS termination, certificate issuance, internet account verification, password reset, distributed abuse controls, monitoring or production readiness. No public deployment or external notification/provider action occurred in these independent tests.
