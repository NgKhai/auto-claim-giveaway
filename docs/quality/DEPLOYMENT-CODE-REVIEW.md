# Independent deployment-guards code review

Reviewed 2026-11-06 against baseline `8528567` and `docs/product/DEPLOYMENT-GUARDS.md`. Scope: `hunter/config.py`, application middleware/cookie integration, deployment tests, Docker startup command and configuration documentation. The reviewer changed no application code.

## Verdict

Accept this configuration-guard increment after final integration and QA checks on the saved files. No unresolved critical/high defect was identified. This is an application configuration boundary, not verified public hosting, TLS/proxy operation, complete authentication hardening or production readiness.

Immutable settings validate environment names, exact host lists, trusted HTTPS origins, production Secure-cookie configuration and explicit absolute database storage. Wildcards, empty CSV entries, host URLs/ports and invalid origin authority/path/query/fragment/credentials fail startup. Origin hosts must belong to allowed hosts. Errors omit supplied configuration values. Production cookie policy uses the validated immutable settings rather than rereading environment variables per request.

The outer host middleware requires exactly one Host header, validates its authority grammar and performs exact normalized host matching before application handlers. Production unsafe requests validate supplied Origin against the configured set rather than trusting a matching request Host. Duplicate/empty Origin values are rejected. Requests without Origin retain the authenticated mutation CSRF requirement. Existing Fetch Metadata checks remain in place.

Production rejects HTTP application routes, with the documented `/api/health` exception. Successful responses receive HSTS and production session cookies are Secure, HttpOnly and SameSite Strict. These controls require a correctly reported ASGI scheme and an independently validated HTTPS deployment.

## Findings and disposition

| Finding | Severity in this scope | Disposition |
| --- | --- | --- |
| Initial authority parsing relied on permissive `urlsplit`, allowing bracket suffixes, interior control-character normalization and explicit empty ports | Important fail-closed acceptance defect | Fixed: shared strict raw authority grammar rejects these inputs before canonicalization; independently checked after fix |
| Ambiguous duplicated Origin headers and empty supplied Origin could evade single-header/nonempty validation | Important acceptance defect | Fixed: duplicated or empty supplied Origin rejected; inspected final middleware and regression checks |
| Default Uvicorn trusts forwarding headers from loopback, which application-only ASGI tests cannot detect | Important deployment boundary found by QA | Shipped Docker/local commands now specify `--no-proxy-headers`. Operations explicitly requires an intentional exact-trusted-proxy override and isolation/header-rewrite verification before HTTPS proxy use |

No valid browser-origin cross-site authorization bypass was demonstrated from the original malformed-authority cases. They were still defects in the promised strict parsing boundary and were fixed before acceptance.

## Independent verification

Executed direct parser and ASGI host-middleware probes against the final parser:

- **11 malformed origins rejected**, including bracket suffix, empty port, embedded tab/newline, credentials, path, query, fragment and invalid port range.
- **Two canonical origin checks passed**: uppercase DNS/default HTTPS port normalization and expanded IPv6 with a nondefault port.
- **Six Host cases passed**: malformed bracket suffix, empty IPv6/DNS ports and duplicate Host rejected; uppercase DNS with port and bracketed IPv6 with port accepted.

Inspected regression tests for invalid production settings, immutable settings/replacement validation, hostile Host/Origin, HTTPS cookie/HSTS flags, absent-Origin CSRF and development compatibility. Full suite, browser and real Uvicorn forwarding-probe execution are separate QA/lead evidence; this reviewer does not claim independently running those checks.

The README and Docker command disable proxy-header interpretation explicitly. Operating instructions correctly explain that direct Uvicorn defaults can trust loopback, that an exact proxy allowlist is needed when deliberately enabling forwarding, and that actual TLS termination remains unvalidated. An app unit test with a synthetic HTTPS ASGI scheme does not prove a real TLS connection.

## Remaining release boundaries

The container command is a safe starting point, not a working production HTTPS deployment: production HTTP routes intentionally fail until reviewed TLS arguments or a validated trusted terminator are configured. No wildcard proxy trust is introduced. Absolute database paths do not establish mounted durable storage, backup/restore or migration safety. Hosted identity, verification/reset, distributed abuse limits, privacy retention operations, secrets, dependency locking, monitoring and real deployment/rollback remain separate gates.

## Container follow-up review

The lead reported a successful BuildKit build and 65 passing container tests as the non-root `hunter` user after an initial permission failure. This reviewer inspected the resulting Dockerfile changes and did not rerun that build or suite.

The optional `proxy_ca` BuildKit secret is mounted only for the dependency-install RUN instruction. When present, `PIP_CERT` points pip at that mounted trust bundle; certificate verification remains enabled. The certificate file is not copied into a layer, and the shell export does not create a persistent image environment variable. Without the secret, pip retains its normal certificate configuration. The frontend syntax declaration enables the secret-mount instruction.

`COPY --chown=hunter:hunter` gives the runtime user ownership of the copied application and web files, resolving unreadable root-owned files inherited from restrictive workspace permissions. The application remains non-root, its database directory belongs to that user, nested Python caches are excluded from the build context, and `--no-proxy-headers` remains in the startup command. No new high defect was identified in this scoped change.

The lead's container-test result is build/runtime compatibility evidence, not production deployment evidence. Runtime HTTP smoke was pending when this addendum was written. Base-image digest pinning, a transitive dependency lock, actual TLS/proxy configuration, durable storage and operational checks remain separate gates.
