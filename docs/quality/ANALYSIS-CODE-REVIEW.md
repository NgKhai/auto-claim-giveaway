# Independent cited-checklist code review

Reviewed 2026-11-06 against baseline `c502cd9`, `docs/product/ANALYSIS.md` and the M5 plan. Scope: `hunter/analysis.py`, analysis API/export integration, related tests and frontend checklist/cache behavior. This reviewer made no application-code changes.

## Verdict

Accept the bounded deterministic checklist increment after final integration/QA checks of the saved files. No unresolved critical/high defect was identified after the grounding fixes below. The result is a candidate checklist for one supported document grammar, not verified eligibility, general semantic extraction, an LLM integration or permission to register.

The authenticated GET reads only the caller's stored source evidence, performs no fetch or persistent mutation, and shares its derivation with account export. No new analysis database state is introduced. Account/source deletion removes the inputs; another owner's evidence cannot fill missing caller evidence. Existing executable opportunities and approval policy remain independent from this endpoint.

Candidates require a fresh, untruncated, error-free excerpt, one supported qualification section and exactly one supported observation for each of the four requirements. Unsupported text, missing/duplicate observations and recognized conflicts abstain. HTML/raw contexts and Liquid control tags are conservatively rejected; exact curated inline data tokens remain raw text. Code fences retain opener character/length and require a valid closing fence. This intentionally narrow grammar may reject legitimate changed provider wording rather than invent a requirement.

Citation quotes retain unmodified excerpt text. Their offsets are zero-based, end-exclusive Python Unicode code-point indices; hash identifies the full fetched body while offsets address the stored excerpt. The frontend renders the supplied quote as text and labels Unicode offsets; it does not slice JavaScript UTF-16 strings using those offsets. Source URL, hash, retrieval time and extractor version accompany citations. User eligibility, deadline and automation permission remain unknown.

## Findings and fixes

| Finding | Severity in this scope | Disposition |
| --- | --- | --- |
| Initial parser emitted partial candidates despite missing requirements or recognized conflict, and silently collapsed duplicate bullets | High grounding/acceptance defect | Fixed: require exactly one observation for every field before publishing any candidates; all claims abstain otherwise |
| Initial fence tracking allowed a shorter closing fence to end a longer opener, making a code example appear factual | High grounding defect | Fixed: track fence character and length and require a valid closing tail |
| Qualification-like text inside HTML comments/raw blocks or Liquid comment/raw blocks could produce candidates | High grounding defect | Fixed: conservatively reject unsupported HTML and Liquid control contexts |
| NaN timestamps could evade numeric age comparisons | Medium malformed-evidence defect | Fixed: finite numeric timestamps only, excluding bool; valid lowercase 64-character hash required |
| Browser-cached candidates could outlive the 24-hour evidence boundary on an open page | Medium freshness defect | Fixed: age-aware snapshots and scheduled evidence expiry invalidate cached candidates and show refresh guidance |
| Initial UI displayed generic unknown text without specific abstention reasons | Medium usability/acceptance defect | Actionable reason mapping added; unknown backend codes retain a safe manual-review fallback |

Frontend requests use account epochs, pending-request identity and source hash/retrieval/snapshot comparison. Refresh invalidates pending analysis and cached results; a changed evidence snapshot discards mismatched responses. Quotes, provenance and reasons use text nodes, and the checklist adds no external registration action.

## Independently executed evidence

The reviewer reproduced the original partial/miscontext extraction defects: missing age produced three candidates, duplicate age four, and a mismatched fence or HTML comment four. These were communicated directly to implementation before acceptance.

After the fixes, independent probes passed for **six grounding cases**: missing age, duplicate age, mismatched fence, HTML comment, Liquid comment and Liquid raw block all returned unknown with zero candidates. **Three malformed timestamp cases** (NaN, infinity and bool) returned invalid evidence. **Four exact citation slices** matched their supplied quotes with an emoji/non-ASCII prefix in the source excerpt.

`python -m unittest discover -s tests -p test_analysis.py -v`: **five tests passed** against the final parser context fixes. Final parser, API ownership/export predicates, frontend cache-expiry/epoch guards and safe text rendering were inspected. Full API regression, actual browser behavior and any live upstream analysis are separate lead/QA evidence; this reviewer does not claim independently executing them. `git diff --check` passed during review.

## Boundaries

Passing curated patterns does not establish document-level completeness or absence of arbitrary contradictions elsewhere. The parser does not evaluate Markdown/Liquid generally, infer eligibility from profile email/country, discover new opportunities, or determine provider automation rules. Any live excerpt that is truncated, changed beyond supported grammar, stale or unsuccessfully refreshed must remain unknown. General extraction, relevance evaluation, hosted identity, real adapters and production operational gates remain unfinished.
