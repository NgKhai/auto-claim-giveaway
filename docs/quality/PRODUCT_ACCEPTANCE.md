# Product acceptance — local research and manual tracking increment

Date: 2026-10-30 (Asia/Bangkok). Reviewer: PM agent, separate from implementation and QA. Scope: initial account → goal → research lead → local tracking → recheck/cancel journey. This review does not cover subsequent discovery changes.

## Decision

**Accept the bounded development increment for integration, subject to root recording its verified commit and push. Do not mark the full M1 scope, the full product or a production release Done.**

The user can create an account, save a goal/profile, search a small research catalog, inspect linked evidence, understand why manual action is needed, track and cancel a lead, and return to persisted state. The interface explicitly says these are reference sources rather than verified active offers and that external registration is unavailable. `Recheck eligibility` does not misleadingly promise approval or submission. Deletion is explicitly limited to application-database records.

The user's full autonomous-product objective remains the governing requirement. Accepting this increment does not reduce the roadmap to a catalog application.

## Evidence reviewed

- PRD, SRS, roadmap, current routes and authentication/dashboard/error templates.
- [Independent QA report](REPORT.md): 28 passing tests; actual Chromium signup, goal, search, tracking, review, cancellation, mobile overflow, logout/login and persistence journey passed. This PM review relies on that execution evidence and does not claim to have rerun tests.
- Root integration result: container build and actual container health, signup, session, CSRF and persisted-goal checks passed after correcting copied application-file ownership. SQLite online backup, integrity check and restored goal count passed. This is local evidence, not production deployment or complete disaster-recovery validation.

## Roadmap task mapping

| Task | Product disposition at this boundary | Remaining work before full task Done |
| --- | --- | --- |
| T01 | Requirements/architecture artifacts reviewed | Root commit/push and progress recording |
| T02 | Initial boot, identity, isolation and profile verified | Full versioned migration progression/rollback, production configuration and auth-hardening validation |
| T03 | Bounded goal creation/viewing accepted | Root commit/push; edit/delete goals remain outside this narrow increment and broader FR-02 remains partial |
| T04 | Labeled reference catalog, linked evidence and local intent accepted | Retrieval timestamps, evidence freshness/conflicts, live source verification and explicit matching rationale |
| T05 | Manual/restricted eligibility decisions accepted | Full provider/action/data scopes, current evidence gate, deterministic allow and versioned audit references |
| T06 | Unique local tracking, recheck and cancellation accepted | Payload-bound approval, actual takeover/execution states, changed-action invalidation and receipts |
| T07–T10 | Not accepted in this increment | Live ingestion, semantic interpretation, reviewed browser execution and submission reconciliation |
| T11–T12 | Local notification records only; partial | Mark-read, durable monitoring, delivery states and tested email/Discord integration |
| T13 | Profile changes and account deletion accepted; partial | Export, retention/backup-deletion disclosures and pending-job cancellation once jobs exist |
| T14 | Local setup/container/backup evidence accepted; partial | Observed remote CI, production deploy, rollback, load and operational alerts |
| T15 | Not accepted | Complete live critical journeys plus independent release QA/PM approval |

No task is labeled Done here because the common Definition of Done includes commit/push evidence owned by root. PR/FR requirements with broader criteria remain partial even where a narrower user journey passes.

## Product limitations to retain visibly

Saved goals currently do not automatically drive discovery; the user must enter a separate keyword query. Matching is keyword overlap, not semantic interpretation. The three catalog items are research sources, not concrete available rewards. These limitations are acceptable for the explicitly labeled initial workspace, but must be resolved or clearly described before broader discovery acceptance.

The automation checkbox is only a future preference; it must not be treated as scoped authorization. No external registration, receipt, provider approval or reward has been demonstrated. Missing/unknown eligibility is distinct from verified eligibility.

Notifications cannot yet be marked read, and account data cannot yet be exported. Deletion from the primary database does not establish deletion from operational backups. These remain retained requirements, not implicit exclusions.

## Next product priority

Deliver a constrained permitted-source ingestion increment with persisted retrieval time, source identity, unverified-provider status and failure/staleness behavior. Integrate it into the existing search/tracking flow and independently review it before proceeding to semantic matching or registration execution. Keep unsupported external actions unavailable until authorization, provider permission and receipt contracts are implemented and verified.
