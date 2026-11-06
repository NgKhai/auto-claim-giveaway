# Operations and release gates

## Local development
Use a single Uvicorn process in the repository root. Dependencies are pinned at the directly used library level; a fully transitive, hash-verified lock remains a release gate. Do not log passwords, cookie tokens or personal payloads. No provider credentials are required for sandbox.

Use the existing isolated cloud checkout; no worktree is required. Persistent files survive snapshots, processes do not. Restart Uvicorn for each task and verify GET /api/health plus the authenticated sandbox journey; an open port alone is insufficient.

## Production gates (not yet validated)
Use HTTPS with Secure cookies, trusted host/origin configuration and a reverse proxy with body-size limits. Validate effective login throttling, signup abuse controls, password reset and operational session/retention controls before public exposure. Local account deletion invalidates all owner sessions, but production backup-erasure and retention procedures remain unvalidated. No uncontrolled URL fetch or arbitrary generated-code executor is permitted.

SQLite is limited to single-instance release evaluation. Before distributed workers, introduce PostgreSQL and schema migrations, transaction-based claim/receipt locking and recovery tests. Never infer external submission success after a timeout; store unknown and reconcile before retry.

Provider adapters need explicit domain/action/field authorization, permission expiry, automation-terms evidence, controlled browser sessions, egress restrictions, CAPTCHA/OTP handoff, payload fingerprint verification and provider-specific receipt reconciliation. A sandbox receipt is not a provider benefit.

## Backup and rollback procedure to validate
Stop application writes, take a SQLite online backup using Python sqlite3.Connection.backup, store it encrypted outside the runtime, and record application commit and schema version. Restore to a different path and run integrity_check and functional checks before switching traffic. Retain previous deployment artifacts. On rollback, verify schema compatibility; never blindly restore an old binary over an incompatible database. This procedure is documented, not a claim of a tested production restore.

## External blockers
Restricted command execution initially could not reach the proxy on port 8080. A read-only git ls-remote succeeded with approved network execution; existing injected GitHub authentication works and no replacement token was requested. Push permission must still be verified separately. Public hosting, DNS/TLS, live-provider permissions, AI model credentials and notification credentials have not been supplied or verified. Do not publish externally until these and release gates are satisfied.

## Container artifact
`Dockerfile` is a deployment starting point, not a verified production deployment. Local build and registry access were validated during AUTH-01b; non-root runtime and HTTP health/UI/static checks passed. Production hosting and registry publication remain unverified. Persist `/app/.data` to a protected volume; terminate TLS before exposing the application. Verify non-root execution, health checks, backups, Secure-cookie configuration and release gates before hosting. Pin the base image digest and produce a transitive dependency lock/SBOM in the release pipeline.

GitHub CI observation: `gh run list --repo NgKhai/auto-claim-giveaway --branch work` returned `Forbidden` from the GitHub API. Git read/push succeeded separately; that does not grant Actions API access. CI results are unverified remotely; local equivalent checks have executed.

## Read-only source connector

SRC-01a requires only HTTPS to `raw.githubusercontent.com` through inherited proxy/CA trust, with TLS verification enabled. The fixed GitHub Education document is the only fetch target; docs.github.com and license URLs are outbound links for the user's browser, not automatic crawler destinations. No user profile/session data is forwarded to the document host. No model or provider credentials are required. Registry changes require reviewed code and new tests, not user-provided URLs.

Source evidence and attempt/cooldown metadata are account-owned SQLite data included in export/deletion. Failures retain previous success and are shown separately from evidence age. Freshness indicates retrieval age, not verification of the user's eligibility or currency of every provider statement. Refresh is explicit and rate-limited; this is not a background monitoring service.

## Production configuration guard (AUTH-01b)

Set all of the following for a production runtime, using your actual hostname and protected mounted database location:

```sh
HUNTER_ENV=production
HUNTER_ALLOWED_HOSTS=hunter.example.com
HUNTER_TRUSTED_ORIGINS=https://hunter.example.com
HUNTER_SECURE_COOKIE=1
HUNTER_DB_PATH=/app/.data/hunter.sqlite3
```

These are non-secret example values, not a deployed host. Use the container's writable protected `/app/.data` volume or a verified equivalent; an absolute filename does not prove persistence. Invalid settings must stop startup. HTTPS termination, trusted proxy peers and forwarding rules still require deployment validation. Do not pass `--forwarded-allow-ips '*'`. HSTS affects future browser access to a host; enable production only when HTTPS is operational. No HSTS preload or includeSubDomains guarantee is made.

Development mode is limited to localhost/loopback and the testserver host. For a public custom hostname, configure a reviewed production environment; do not add a wildcard to evade host validation. Native API clients without Origin still need authenticated CSRF tokens for state changes. Production configuration safety does not supply account verification, password recovery, distributed abuse protection or a complete identity lifecycle.

Production rejects plain HTTP except internal /api/health. Configure the trusted HTTPS terminator so Uvicorn receives HTTPS scheme from trusted peers; raw client-supplied forwarding headers are not trusted by the application. Verify public HTTP cannot reach authenticated routes. Health is a narrow HTTP exemption for local container readiness, not a public administration endpoint.

The shipped container command disables proxy headers with `--no-proxy-headers`. Keep that default for direct TLS termination at Uvicorn (supply reviewed TLS arguments separately). For an HTTPS reverse proxy, explicitly override the command to enable `--proxy-headers --forwarded-allow-ips <exact-trusted-proxy-IP>` after verifying network isolation and header rewriting by that proxy. A direct default Uvicorn command trusts loopback proxy headers; do not use that default as evidence of forwarding protection. Application tests use ASGI schemes; actual proxy/TLS termination remains a deployment acceptance gate.

## Container validation evidence (2026-11-06)

Build used the managed local Docker daemon, inherited proxy and optional BuildKit secret `proxy_ca` mapped from the public system CA bundle. `PIP_CERT` applies only inside the networked RUN step; session CA files are not copied to image layers. Standard builds without that secret use normal pip trust. Reproduce in the managed environment with `docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t opportunity-hunter:validated-local .` after checking the correct local daemon per runtime instructions.

The initial container test run failed because root-owned COPY artifacts preserved restrictive source permissions. `COPY --chown=hunter:hunter` resolved the source/static ownership issue. The rebuilt image `sha256:6b22860a2dcae511cc14ae4583e749130bc4be5b192e00bbf43e536768b3c214` passed all 65 tests under UID1000 with tests mounted read-only. Its default process returned HTTP200 for /api/health, / and /static/app.js. Temporary test containers were removed. Dependency installation resolved newer transitive versions than the host venv; both suites passed. Fully hashed dependency locking, immutable base-image pins, SBOM, image publication and production deployment remain separate gates.
