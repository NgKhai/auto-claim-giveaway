# Independent QA — ANA-01a deterministic source checklist analysis

Decision: accept the tested citation-bound, read-only analysis increment. General AI analysis, user eligibility, external registration and production release remain unaccepted.

## Executed evidence

- Initial independent run: seven test methods produced 11 expected failing assertions/subcases because the analysis route did not exist (404). This was a behavioral red baseline, not a parser failure or upstream network problem.
- Final independent `python3 -m unittest discover -s tests -v`: **78/78 passed**, 8.009 seconds, including eight new independent analysis API methods and five developer analysis tests alongside the previous 65 tests.
- `python3 docs/quality/analysis_browser_smoke.py`: **passed**, final run 5.815 seconds, actual Chromium against an injected deterministic source transport. Covers missing-evidence unknown, exact four candidate quotes, source hash/extractor provenance, inert adversarial quote text, already-open evidence expiry clearing candidate quotes, stale refresh-required state, and delayed prior-owner response discarded after another account signs up. No JavaScript errors observed.

The browser script is separate from and preserves existing smoke scripts. It requires optional Playwright and `/usr/bin/chromium`, creates a temporary database/localhost process and terminates its process. These are deterministic session checks, not live-provider or CI-browser evidence. Latest root integration runs record subsequent revisions and existing-browser results separately.

## Independent API coverage

| Area | Observed result |
| --- | --- |
| Authentication, unknown source and missing evidence | Authentication required; unknown ID rejected; no evidence returns unknown/null values and no fetch |
| Citation precision | Each quote equals the exact end-exclusive Python Unicode-codepoint slice, including an emoji/Vietnamese prefix; source URL, successful timestamp, hash and extractor version match cached evidence |
| Candidate values | Age from recognized provider text; three other recognized requirements have boolean true; eligibility/deadline/automation remain unknown |
| Read-only behavior | Repeated analysis requests make no network calls, create no audit rows and leave stored source records unchanged |
| Updated source | Changed body changes hash and age citation/value to the new successful source; old provenance is not reused |
| Incomplete/ambiguous context | Missing, truncated, unsupported or negated qualification wording abstains; conflicting recognized ages cannot select a convenient age; fenced examples, blockquotes and duplicate sections do not create candidates |
| Freshness/error | Stale source and latest refresh failure return needs_refresh with unknown/null claims and no citations |
| Ownership/privacy | Another account initially sees no evidence; each export contains its own analysis; deleting one account removes access while the other account retains its own derived result |
| Execution boundary | Real-source ID cannot create an executable sandbox application; analysis creates no registration |

## Browser fixture boundaries

The candidate/provenance steps use the actual backend parser on a canonical deterministic source fixture. A separate intercepted analysis API response deliberately substitutes HTML/script-looking citation text to test frontend rendering as text. That substitution does not claim the parser accepts such a noncanonical citation. No script/image DOM nodes or injected-host requests appear, and no injected JavaScript executes.

For account switching, the browser genuinely holds an Alice analysis response, logs Alice out, creates Bob, then fulfills the old response. Bob's card retains no Alice analysis and his own analysis remains unknown. Open-page expiry is tested by a near-boundary stored retrieval time: candidate quotes appear while fresh and disappear after the 24-hour boundary without reloading.

## Limits

This is a versioned fixed-pattern extractor for four known GitHub Education qualification bullets, not semantic search, an LLM, arbitrary-language contradiction detection or verified user eligibility. Unknown text must not imply absence of requirements. A stored excerpt may omit relevant context; unknown/stale/error outcomes require manual review or source refresh. Raw Markdown/Liquid remains unexpanded.

No automated registration, reward, monitoring, notification delivery, hosted deployment, realistic load measurement or production security certification follows from these tests. Live source evidence and any actual provider behavior must be documented separately.
