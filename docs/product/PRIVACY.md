# AUTH-01 addendum: local account export and deletion

Status: implemented and independently verified for the local slice; see quality/PRIVACY-REVIEW.md and PRIVACY-CODE-REVIEW.md. Date: 2026-11-05. This slice extends the accepted local sandbox; it is not completion of Internet-facing authentication hardening or production retention operations.

## User value and boundaries

An authenticated user can export their own stored account information and permanently remove their local account. The interface explains the scope before either operation. Export contains only the current account's profile, goals, applications and audit events. Deletion affects the application's local database and all sessions for that account. It does not delete a third-party provider account, reverse a registration or establish deletion from operational backups.

No real email, provider request or notification is sent by either operation. Production retention schedules, backup expiration, legal retention and restore-time deletion reconciliation remain separate OPS/privacy release work.

## Export contract and acceptance

- Require an authenticated, unexpired session; derive the account owner from that session rather than a client-selected account ID.
- Return a structured downloadable JSON representation of the owner's profile, goals, applications and audit events, with schema/version and export time sufficient to understand the file.
- Include only permitted user-facing data. Exclude password hashes/salts, session records, raw session cookies/tokens, CSRF tokens and internal approval authentication material.
- Preserve useful application statuses, payload and sandbox receipts without implying provider fulfillment. Clearly explain that the download may contain personal information and should be stored privately.
- A different account's data must not appear, including when records reference applications or goals. Unauthenticated and stale-session requests are denied without disclosing account data.

## Destructive deletion contract and acceptance

- Require a live authenticated session, valid session CSRF token, correct current password and explicit UI confirmation that local account data will be permanently removed.
- Reject missing/incorrect password, missing/incorrect CSRF and cross-account targeting without deleting any data or invalidating unrelated sessions.
- Derive the deleted user from the authenticated session; never accept an arbitrary account owner from the request.
- Atomically remove the account and all of its stored goals, applications, audit events and active sessions. Include any account-linked authentication/throttling records that can otherwise retain identifying data. Do not leave ownerless personal records after success.
- Invalidate every session belonging to the deleted account, including the requesting browser and other browsers. Clear the current browser's session state and private view after success. A replay of an old cookie must be denied.
- Preserve all other accounts, their records and their working sessions. Failure partway through storage changes must roll back, not leave a partial deletion reported as complete.
- Display completion only after the server confirms success. Do not claim removal from third-party services or backups. The user can cancel the confirmation without a server-side mutation.

Correct password plus authenticated CSRF-protected request provides the server-side destructive-operation boundary. Explicit consent is additionally a required UI interaction; a local confirmation is not a claim that a browser can cryptographically prove a human clicked it.

## Required independent acceptance tests

SRC-01a extends this contract to owner-scoped source evidence records: include them in owner export and remove them atomically on account deletion, preserving other owners. See [SOURCES.md](SOURCES.md), SRC-A10. This extension remains pending verification until populated-source privacy tests run.

| ID | Case | Expected result |
| --- | --- | --- |
| PRIV-01 | Export with profile, goals, apps and audit | Complete owner-only JSON; required secret/internal fields absent recursively |
| PRIV-02 | Export while another populated account exists | No other account's email, goals, payloads, receipts or activity |
| PRIV-03 | Unauthenticated/expired-session export or deletion | Denied; no data disclosure or mutation |
| PRIV-04 | Delete with missing/wrong password or CSRF | Denied; owner data and sessions remain intact |
| PRIV-05 | Confirm correct deletion | Owner and all dependent local data removed together |
| PRIV-06 | Reuse two previously active owner sessions | Both denied after deletion; stale cookies cannot export or mutate |
| PRIV-07 | Other populated account after deletion | Data unchanged and its session still works |
| PRIV-08 | Browser export and deletion confirmation/cancel | File downloads; cancellation does not delete; successful confirmation returns to signed-out view |
| PRIV-09 | Refresh/restart after deletion | Deleted private state cannot reappear from persistent storage or session recovery |

Run relevant prior authentication, ownership, approval and sandbox-flow regression tests. Record actual commands, outcomes and reviewer disposition before marking this slice accepted. Do not infer deployment, backup erasure or full AUTH-01 completion from these local tests.

## Security throttle migration boundary

New failed-login and deletion-reauthentication records for known accounts carry an owner association and are removed with that account, including attempts from other IPs. Records predating this migration, and attempts for nonexistent accounts, may have a NULL owner and only a pseudonymous SHA-256 rate-limit key. These hashes are not claimed anonymous; a known email/IP may confirm a key. They are ineligible for throttling after 15 minutes and physically removed opportunistically on a later login/deletion-auth request, not by a scheduled erasure service. Legacy owner association cannot be reconstructed safely. Scheduled retention and forensic/backup erasure remain production gates.
