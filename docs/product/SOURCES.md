# SRC-01a: fixed official documentation source

Status: specified, implementation and independent verification pending. This M3 increment adds read-only retrieval of one official document. It does not complete general discovery, semantic search, source verification or external registration.

## Registry and workflow

The sole registry ID is `github-education`. It maps in reviewed server code to:

`https://raw.githubusercontent.com/github/docs/main/content/education/about-github-education/github-education-for-students/apply-to-github-education-as-a-student.md`

The corresponding official repository document is already referenced in `docs/02-opportunity-sources.md`. The lead has reported HTTP 200 read access using existing network policy. A successful read establishes access to a document, not current eligibility, provider permission or a reward.

An authenticated user opens the Sources tab, inspects the fixed source and refreshes it explicitly. The tab displays retrieval status, source URL, excerpt, hash, last successful retrieval, freshness and whether a later successful retrieval changed the content. It remains visibly separate from the executable sandbox opportunity catalogue. There is no external registration action from a source record.

## Retrieval and safety contract

- Accept only the fixed registry ID. Never accept a URL, hostname, path or destination override from a client, model or fetched content. Unknown registry IDs fail before network I/O.
- Use HTTPS with TLS verification and existing session proxy/CA trust. Refuse redirects, including same-host redirects; do not follow links in retrieved text.
- Bound body retrieval to 256 KiB and use a 10-second request timeout. Oversized, timed-out, malformed or failed responses produce an honest error and no successful evidence replacement.
- Read document text as untrusted data. Escape it for display; never run HTML/scripts, template fragments, shell commands or instructions from the document. Links in the excerpt cannot expand tool or network access.
- Apply a persistent 60-second cooldown per owner/source between refresh attempts, including failed attempts. An application restart cannot reset the cooldown. Concurrent attempts cannot bypass the cooldown by racing a timestamp check.
- Require the existing account/session ownership boundary; refresh is an authenticated write protected by CSRF/origin checks. A user cannot select another owner's record.

The fixed immutable registry URL limits the M3 fetch surface; it is not evidence of a general-purpose SSRF defense. Arbitrary-source ingestion, redirect/DNS validation, private-network isolation and browser egress remain future SRC-01 work.

## Persistent evidence and freshness

Each owner/source record stores last-attempt time, successful retrieval time, SHA-256 of the successfully retrieved body, a plain-text excerpt of at most 4,000 characters, content-change state and current error/status. Source data is owned by the account even though the upstream document is public.

Successful refresh replaces hash/excerpt/retrieval time atomically. A later successful refresh compares the new body hash with the previous successful hash. The first retrieval has no prior comparison and must not imply an observed change. Refreshing unchanged content still records the new successful retrieval time.

Freshness derives from the last successful retrieval: less than 24 hours is fresh, 24 hours or more is stale, and no successful retrieval is unavailable. A failure preserves all prior successful evidence and its original timestamp, marks the error and does not reset the freshness clock. The UI must distinguish a fresh cached document from a failed latest attempt rather than hide either fact.

Eligibility, opportunity deadline and permission for automated registration remain **unknown**. Retrieval time is not a provider deadline. A source hash proves which bytes were observed, not legitimacy, eligibility, completeness or authorization. Updating a source must not unlock, approve or submit a registration.

## Privacy extension

Own-data export includes the owner's source records, including retained excerpt/hash/status/times. It excludes any other owner's records and preserves existing exclusions of passwords, sessions, CSRF and internal approval authentication material. Account deletion atomically removes all source records with the rest of that owner's local data and sessions; other owners remain unaffected. Update privacy regression checks to cover populated source records rather than infer coverage from the previous schema.

## Required acceptance tests

| ID | Scenario | Expected result |
| --- | --- | --- |
| SRC-A01 | Successful fixed-source retrieval | Correct registry URL; persisted hash/excerpt/time; source displayed separately from sandbox |
| SRC-A02 | Unknown ID or attempted URL override | No arbitrary network request; only the reviewed fixed destination can be used |
| SRC-A03 | Redirect, timeout, non-success response or oversized body | Honest failure; no follow-up redirect request or evidence replacement |
| SRC-A04 | Refresh failure after prior success | Retained hash/excerpt/success time; error visible; freshness based on previous success |
| SRC-A05 | Identical and changed successful bodies | Hash comparison accurate; first retrieval not falsely labeled changed |
| SRC-A06 | Freshness at/after 24 hours | Fresh/stale/unavailable distinctions correct with explicit timestamps |
| SRC-A07 | Rapid, concurrent and post-restart refresh | Persistent per-owner 60-second cooldown enforced, including failure attempts |
| SRC-A08 | Two accounts and unauthenticated/CSRF-invalid requests | Owner-isolated records; no unauthorized read/write; another owner retains independent cooldown |
| SRC-A09 | Untrusted instruction/HTML content | Displayed as inert text; no tool execution, arbitrary fetch or registration side effect |
| SRC-A10 | Export/delete after source population | Own source record exported; other user's excluded; deletion removes only owner's record |
| SRC-A11 | Browser Sources tab and error state | Human-readable source/evidence/status/unknown fields; no external-submit control |
| SRC-A12 | Existing auth/privacy/sandbox regression | Existing boundaries and receipt behavior remain intact |

Use injected fetch responses for deterministic failure/size/timeout tests; report the live HTTP read separately. A mocked response is not a live provider integration. Record actual QA results and review disposition before acceptance; no test outcome is asserted by this specification.
