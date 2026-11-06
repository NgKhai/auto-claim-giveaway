# SRC-01b: cited deterministic qualification checklist

Status: locally implemented and independently accepted;78 test cases and three Chromium workflows passed. See PROGRESS.md and quality reports for evidence. This is a read-only analysis of the owner's retained GitHub Education source excerpt. It is not an LLM, semantic search, verified eligibility result or provider automation permission.

## Scope and user value

Help the user find recognizable qualification statements in the fixed source without asking them to trust invented summaries. A versioned deterministic extractor recognizes only curated patterns in the GitHub qualification section's bullets: minimum age, current enrollment/student status, documentation proving student status and personal GitHub account. Supported wording and expected qualifiers must be deliberately tested. No general arbitrary-language interpretation or contradiction detection is promised.

The checklist reports candidate requirements from source text, not whether a particular person qualifies. Existing profile country/email is not proof of age, enrollment, documentation or provider approval. Deadline and permission for automation stay unknown. The fixed source cannot become an executable opportunity or authorize sandbox/external registration through analysis.

## API and evidence contract

`GET /api/sources/{id}/analysis` requires the existing account session and uses only that owner's stored source record. It performs no network request, refresh, model call or persistent mutation. Unknown source IDs and unauthenticated requests fail using existing API conventions. Another owner's fresh evidence must never fill a missing record for the caller.

The derived result includes a deterministic extractor version, source ID/URL, evidence body hash and successful retrieval time, analysis state/reasons, and any supported candidate statements. Every displayed statement must cite an exact quote with zero-based, end-exclusive **Unicode character** offsets into the unmodified stored excerpt: `excerpt[start:end] == quote`. Python Unicode code-point indexing defines this contract; clients must not silently reinterpret offsets as UTF-16 code units. HTML escaping or display formatting must not change the underlying citation text. The source hash identifies the fetched full body; offsets identify the stored excerpt, not positions in the full upstream file.

Candidates cannot contain inferred numbers or fabricated paraphrases. If a normalized label/value is included, its corresponding source quote must support it under the documented curated pattern. Preserve qualifying words and alternatives; do not turn an alternative proof option into two universally mandatory requirements. Duplicate/ambiguous/conflicting supported statements must not yield a confident single fact.

## Conservative outcome rules

- No retained evidence: unknown/unavailable; explain that an explicit source refresh is needed.
- Evidence at or beyond the existing 24-hour freshness boundary, latest refresh error, or truncated excerpt: unknown/needs refresh; do not show a current complete checklist or verified result.
- Missing qualification section, missing expected requirement, unsupported/reworded bullet, ambiguous or conflicting recognized facts: unknown/incomplete, with specific supported reasons rather than invented answers.
- A refreshed changed body must be analyzed against its own hash/text. Never reuse old citations or checklist facts. Unsupported changed wording falls back to unknown; a new hash alone is not evidence that facts conflict.
- Only a complete, fresh, untruncated, error-free set matching the version's supported qualification patterns may be displayed as candidate requirements. Even then eligibility, deadline and automation permission remain unknown.

The parser's conflict checks are limited to its supported patterns, such as incompatible recognized age values or differing recognized requirement variants. They cannot certify that an arbitrary document has no contradictions or that other source sections contain no additional requirements. Raw Markdown/Liquid templates remain unrendered untrusted text. A source sentence asking the system to alter permissions or run code is data, never a tool instruction.

## UI and privacy

Render an honestly named candidate checklist in the separate Sources view, with exact quotes, source attribution, hash/retrieval context, limits and actionable unknown/refresh reasons. Do not label it “you qualify,” “verified eligibility,” “AI analysis” or permission to register. Quotes are inert text nodes, not executable markup. Analysis does not add a submit button or change application approval state.

Own-data export includes derived analysis for each owned source record using the same extractor and evidence rules as the GET endpoint. There is no new analysis database state: deleting the account/source records removes the input, so no analysis remains recoverable through an old session or recreated account. Existing secret exclusions, ownership isolation and backup/forensic-erasure limits still apply.

## Acceptance and independent tests

| ID | Scenario | Expected result |
| --- | --- | --- |
| ANA-01 | Fresh complete supported qualification bullets | Four candidate requirement types with extractor version; no user eligibility/deadline/automation claim |
| ANA-02 | Quote spans with punctuation, Markdown and non-ASCII prefix | Exact `excerpt[start:end] == quote`; hash/time/URL match owner's evidence |
| ANA-03 | Section/bullet missing or unsupported wording | Honest unknown/incomplete reason; no guessed fact |
| ANA-04 | Recognized contradictory/ambiguous values or duplicated sections | Conservative unknown, no unsupported arbitrary-language conflict guarantee |
| ANA-05 | Unavailable, stale boundary, failed latest refresh or truncated evidence | Unknown/needs refresh; cached evidence not presented as current complete analysis |
| ANA-06 | Source refreshed with changed body/wording | Citations/hash recomputed; stale quotes never reused; unsupported changes become unknown |
| ANA-07 | Two owners with different/missing retained evidence | Caller sees only own analysis; unauthenticated/unknown-source request rejected |
| ANA-08 | Analysis GET repeated or source cooldown active | No network call, refresh/cooldown update or persistent state mutation |
| ANA-09 | Export and account deletion | Export derivation agrees with GET; other owner's analysis excluded; old/deleted-account sessions denied |
| ANA-10 | Hostile markup/instructions or qualification-like text outside supported section | Inert display; no tool execution or unintended candidate extraction |
| ANA-11 | Existing sandbox submission boundary | Official source/analysis cannot create or authorize an executable external registration |
| ANA-12 | Actual browser checklist/unknown workflow and prior regression | Accurate visible limits/citations/reasons; source/privacy/auth/sandbox behavior preserved |

Use deterministic source fixtures for parser edge cases and report actual upstream behavior separately. Passing these cases is acceptance of the curated parser only; general extraction, semantic relevance, live-provider eligibility and full AI-01 remain unfinished.
