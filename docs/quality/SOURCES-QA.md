# Independent QA acceptance — SRC-01a fixed source reader

Decision: accept the tested read-only fixed-source increment; general discovery, external registration and production release remain unaccepted. This report covers deterministic fixtures. Live upstream evidence belongs in the lead's separate report.

## Actual execution evidence

- Initial independent test run: seven source acceptance cases errored because `create_app(source_transport=...)` did not yet exist. This established a missing prerequisite, not a successful behavioral test or a live network failure.
- Final `python3 -m unittest discover -s tests -v`: **50/50 passed**, 6.864 seconds, including 13 new independent source API cases, 19 prior independent API cases and 18 developer tests.
- `python3 docs/quality/browser_smoke.py`: **passed** the existing actual-Chromium account/goal/consent/sandbox receipt/persistence/audit/mobile/export/deletion workflow after the source UI changes. No JavaScript errors.
- `python3 docs/quality/sources_browser_smoke.py`: **passed** in actual Chromium with an injected transport: initial unavailable state, explicit refresh, exact SHA-256 and excerpt, unknown eligibility/automation text, disabled cooldown, failed next attempt preserving prior evidence, fresh and stale cached-evidence badges while error remains visible, and 390px layout without horizontal overflow. No JavaScript error or injected external request.

Both browser scripts require optional Playwright and `/usr/bin/chromium`. They start their own temporary database/localhost process and clean up the processes they start. Run from the repository root. Browser acceptance is session evidence rather than a claim that CI browser execution occurred.

## Independent coverage and findings

| Boundary | Observed result |
| --- | --- |
| Authentication, CSRF, unknown registry ID and URL override | Rejected before source fetch; explicit client URL is rejected |
| Fixed destination and credential separation | Requested registry host only; no account cookie, Authorization or CSRF header forwarded |
| Evidence | Correct hash and excerpt; first retrieval not marked changed; identical/changed body comparison accurate |
| Retained cache | Failed status/redirect, oversize, malformed UTF-8, wrong media, empty/compressed response preserve prior successful hash/excerpt/retrieval timestamp |
| Redirect | Redirect response produces failure with no second destination request |
| Timeout | Sanitized error does not leak thrown exception text; async slow stream exceeds small test total deadline and leaves no successful evidence |
| Freshness | 86,399 seconds fresh; exactly 86,400 and later stale; failure does not replace timestamp |
| Cooldown | Failed attempts included; persists across app recreation; concurrent attempts produce one fetch and one 429 |
| Ownership | Each account has independent evidence/cooldown; own export includes source state; deletion removes own source rows while another account remains unaffected |
| Deletion race | Delete during held fetch prevents late completion from recreating source records |
| Execution boundary | Official-source ID cannot create a sandbox application; no registration control exists on source card |
| Untrusted text | Literal `<script>`, `<img>` and instruction text appears in a text-only excerpt; no generated DOM script/image, JS execution or injected-host request |

During review, cached-evidence freshness was initially hidden behind an `unverified` latest-attempt status. Backend added independent `evidence.freshness`, frontend renders it separately, and the dedicated browser test now checks both recent and stale cache labels while the latest-attempt error remains visible.

The frontend reported and corrected accidental freshness rendering in sandbox opportunities and delayed old-session response handling; baseline/source browser runs above occurred after those saved changes. These browser runs verify the covered normal journeys, not every possible asynchronous response interleaving.

## M5 browser regression compatibility

The root's final M5 integration run caught a failure in the older Sources smoke assertion that required exactly one button. The source card now correctly includes two reviewed read-only controls: refresh and analysis. The failed assertion conflated the legitimate analysis control with an external registration control; it did not show that registration was enabled.

The test now explicitly requires exactly one refresh control with its reviewed accessible-name pattern, exactly one `Xem điều kiện` analysis control with its dedicated selector, exactly two total controls, and no other button outside that whitelist. This preserves the no-unreviewed-action check rather than disabling it. No application implementation or authorization rule was changed for this correction.

After correction, `python3 docs/quality/sources_browser_smoke.py` passed again in real Chromium, **2.713 seconds**, including the prior inert-content, error/cache, freshness and mobile assertions. No injected external request or JavaScript error occurred. The original 50-test M3 evidence above remains historical; M5's latest API totals are recorded in ANALYSIS-QA.md and the root integration record.

## Limits and remaining gates

A mocked official document is not evidence of current provider content, eligibility, reward availability or automation permission. Retrieved content is raw Markdown with unresolved templates and bounded excerpts; no semantic fact extraction or legitimacy decision is implemented. General arbitrary-source ingestion and SSRF/private-network defenses remain future work; this increment admits only one reviewed URL and rejects redirects.

There is no automated monitoring/scheduler, notification delivery, real registration adapter, CAPTCHA/OTP handoff or production deployment in this acceptance. The hash identifies retrieved bytes; it is not proof of legitimacy or permission. Logical database deletion does not establish backup or forensic erasure. No realistic load benchmark or production security certification is claimed.
