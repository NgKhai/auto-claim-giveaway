# Operations and release gates

## Local development
Use a single Uvicorn process in the repository root. Dependencies are pinned at the directly used library level; a fully transitive, hash-verified lock remains a release gate. Do not log passwords, cookie tokens or personal payloads. No provider credentials are required for sandbox.

Use the existing isolated cloud checkout; no worktree is required. Persistent files survive snapshots, processes do not. Restart Uvicorn for each task and verify GET /api/health plus the authenticated sandbox journey; an open port alone is insufficient.

## Production gates (not yet validated)
Use HTTPS with Secure cookies, trusted host/origin configuration and a reverse proxy with body-size limits. Validate effective login throttling, signup abuse controls, password reset, session invalidation and account deletion before public exposure. No uncontrolled URL fetch or arbitrary generated-code executor is permitted.

SQLite is limited to single-instance release evaluation. Before distributed workers, introduce PostgreSQL and schema migrations, transaction-based claim/receipt locking and recovery tests. Never infer external submission success after a timeout; store unknown and reconcile before retry.

Provider adapters need explicit domain/action/field authorization, permission expiry, automation-terms evidence, controlled browser sessions, egress restrictions, CAPTCHA/OTP handoff, payload fingerprint verification and provider-specific receipt reconciliation. A sandbox receipt is not a provider benefit.

## Backup and rollback procedure to validate
Stop application writes, take a SQLite online backup using Python sqlite3.Connection.backup, store it encrypted outside the runtime, and record application commit and schema version. Restore to a different path and run integrity_check and functional checks before switching traffic. Retain previous deployment artifacts. On rollback, verify schema compatibility; never blindly restore an old binary over an incompatible database. This procedure is documented, not a claim of a tested production restore.

## External blockers
Restricted command execution initially could not reach the proxy on port 8080. A read-only git ls-remote succeeded with approved network execution; existing injected GitHub authentication works and no replacement token was requested. Push permission must still be verified separately. Public hosting, DNS/TLS, live-provider permissions, AI model credentials and notification credentials have not been supplied or verified. Do not publish externally until these and release gates are satisfied.

## Container artifact
`Dockerfile` is a deployment starting point, not a verified production deployment. Build and registry access have not been validated in this environment. Persist `/app/.data` to a protected volume; terminate TLS before exposing the application. Verify non-root execution, health checks, backups, Secure-cookie configuration and release gates before hosting. Pin the base image digest and produce a transitive dependency lock/SBOM in the release pipeline.
