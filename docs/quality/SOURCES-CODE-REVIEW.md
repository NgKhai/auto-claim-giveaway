# Independent SRC-01a code review

Reviewed 2026-11-06 against baseline `c82e9a8`, `docs/product/SOURCES.md` and the M3 plan. Scope: `hunter/sources.py`, source API/storage/privacy changes, frontend source display and source regression tests. This reviewer changed no application code.

## Verdict

Accept the fixed read-only source slice after final integration/QA checks of the saved files. No unresolved critical/high defect was identified after the fixes below. This verdict applies to one reviewed public document, with sandbox registration remaining separate. It does not establish general discovery, semantic extraction, eligibility verification, automation permission or production readiness.

## Findings and disposition

| Finding | Severity | Resolution |
| --- | --- | --- |
| Initial synchronous retrieval checked elapsed time only after `iter_bytes(chunk_size=4096)` yielded. A tiny body trickle could keep inactivity timeouts alive and delay that check far beyond ten seconds | High resource-bound defect | Fixed: asynchronous HTTP retrieval enclosed in `asyncio.timeout(TIMEOUT)`, covering headers and body, including buffered iteration. Independently retested with real async slow chunks |
| Failed latest attempt collapsed retained evidence age into an unverified status, making a fresh cache appear stale/non-current | Medium truthfulness defect | Fixed: independent `evidence.freshness` based on successful retrieval time, displayed separately from latest refresh error |
| A delayed 401 from an old account's in-flight refresh could invoke the generic API logout handler after another account signed in | Medium session/UI defect | Fixed: API helper captures the request's authentication epoch and mutates current login state only when the epoch still matches; source completion also checks its epoch |

The sole source ID maps to the exact reviewed HTTPS raw GitHub document in server code. Request payload forbids unknown fields; a client cannot provide a destination. Redirects are disabled and non-200 responses fail. No fetched links, scripts, Liquid templates or instructions are evaluated. Transport keeps environment proxy/CA trust and TLS verification; user cookies, CSRF and credentials are not forwarded.

Retrieval rejects non-text media types and non-identity content encoding before reading a body. Refusing compression avoids uncontrolled decompression. The accepted byte buffer is limited to 256 KiB, UTF-8 decoding is strict, the stored excerpt is limited to 4,000 characters, and SHA-256 covers the complete accepted body. Excerpt truncation and raw-template limitations are explicit. Attribution/license links are supplied from the reviewed registry.

The refresh route derives ownership from the authenticated session and requires existing CSRF/origin checks. A short `BEGIN IMMEDIATE` transaction claims the persistent owner/source cooldown before network I/O. Network work occurs after commit. The result write verifies both surviving owner ID and attempt token; account deletion cannot recreate state or attach results to a newly registered account with the same email. Failures retain previous successful hash/excerpt/time, and first retrieval does not imply observed content change. Source records are included in owner-only export and atomically removed by account deletion.

The UI renders excerpts and errors as text nodes, separates source evidence from the sandbox catalog, displays cached freshness alongside latest failure, and marks eligibility/deadline/automation permission unknown. Source retrieval cannot unlock application approval or submission. There is no external-submit control on source cards.

## Independently executed evidence

- Reproduced the initial timeout defect with a mock byte stream: 100 one-byte chunks each advanced a simulated clock by one second; the initial implementation consumed all 100 before reporting timeout.
- Retested the fix using a real asynchronous stream yielding one byte every 5 ms, with the timeout scaled to 60 ms: it returned `upstream_timeout` after **62 ms**, having consumed **11 chunks** instead of the available 1,000. This confirms cancellation before a 4,096-byte iterator flush.
- Paused an authenticated refresh in body I/O, deleted that account, registered a replacement with the same email, then released the old fetch. Deletion returned **200** during the paused fetch, replacement registration **201**, old fetch **401**, and the database retained **zero source rows**. This verifies the absence of a database write lock over network I/O and no owner-state resurrection.
- Inspected final request-epoch guards, evidence-freshness display and source storage/privacy predicates. `git diff --check` passed at review time.

Dynamic API probes used temporary databases, injected HTTP transports and approved execution outside restricted IPC. The reviewer did not perform a live upstream retrieval or independently rerun the full browser/suite; those separate results belong in the lead/QA evidence. The tests inspected cover cooldown races and restart persistence, exact destination, redirect rejection, error retention, byte limits, invalid content, freshness boundary, account isolation and source privacy.

## Limits

This fixed registry constrains the available destination; it is not a reusable SSRF defense for arbitrary URLs. Any future dynamic source registry needs separate redirect/DNS/private-network/egress validation and permission review. Public source retrieval reveals server network metadata to the upstream/proxy, but carries no account payload. A successful read and hash establish observed document bytes, not verified eligibility, completeness, authorization or a reward.

The per-account cooldown and ten-second request deadline do not replace global production outbound concurrency/abuse limits. Multi-replica storage, operational monitoring, production deployment, evidence extraction/evaluation and browser/provider adapters remain separate release gates.
