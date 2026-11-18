# S06 drafting verification — work in progress

18 November 2026. **Not delivered.** Live DeepSeek compatibility, token accounting and answer-quality evaluation remain pending a locally configured key. No paid request has been made.

## Implemented and verified locally

- Durable generation runs create Draft revisions, never Messages, approvals or sends. Public API is fixture-only. Sources/access/ticket revision are checked before and after generation. Stale outcomes are discarded, cancellation preserves previous drafts, and interrupted provider jobs are not retried automatically.
- Human edits create another revision retaining generation/citation provenance. Composer citation controls open authenticated exact source passages. Provider responses are validated for envelope, schema, authorized citation IDs and required evidence.
- Local-only DeepSeek path requires explicit LIVE_AI_ENABLED, DEEPSEEK_API_KEY, loopback endpoints and an active synthetic Admin workspace. Conservative PostgreSQL reservations serialize monthly/session spending before provider calls; token usage releases unused reservations. Unknown acceptance retains full allocation. Pricing details and official sources: [provider notes](../planning/s06-provider.md).

Post-implementation `uv run python -m scenarios.s06`: **23 real HTTP/PostgreSQL/worker assertions passed**, covering fixture/escalation drafts, concurrent worker claims, idempotent queued requests, cancellation, editing/provenance, stale ticket/source rejection, foreign workspace and Viewer rules, request/month/session accounting and concurrent monthly reservations. Uses actual sessions and PostgreSQL; scenario-owned data is deleted.

`uv run python -m scenarios.s06_provider`: **13 local HTTP provider-contract assertions passed**. Canned transport responses explicitly verify bounded structured requests, citation/schema checks, refusal/incomplete/unknown-usage handling, malformed envelopes and protection against sending real credentials to the local fixture. These are not live DeepSeek results or AI quality measurements.

Ruff, Pyright, ESLint, TypeScript and production build passed during implementation. Fresh disposable PostgreSQL upgrade → downgrade to S05 → upgrade passed. Final branch CI is pending.

## Ego-browser verification

Guide 2.2.1. Reused the prior synthetic S05 workspace and published PDF. Verified generation into the composer, opening its exact cited PDF page, editing and saving a new revision with retained citations, reloading while queued, and displaying the previous saved draft while work remains pending.

Stopped the project API to exercise a genuine connection failure: the UI preserved the previous draft and exposed **Refresh generation status**. Restarted the API, processed the actual fixture worker job, and refreshed: the newly saved draft reached the composer, the error cleared and editing became available. This directly verifies the reviewed completion/resume/recovery fixes.

Five widths (360, 390, 768, 1280, 1440) in both themes had no horizontal overflow. Screenshots visually inspected:

- [Light source inspection](images/s06-source-light.png)
- [Dark mobile generated composer](images/s06-mobile-dark.png)

Real maintained authentication limits were encountered after combined scenario/browser work. Waited for reset without bypass. Native 200% zoom remains unverified.

## Independent review

Separate Standards and Spec agents reviewed `ea41f16...100237f`. Findings: terminal-state updates aborted detail refresh; resumed runs were incorrectly marked applied; polling had no recovery; malformed provider envelopes could stop the worker. Fixed in `1743d13`, independently rechecked clear. DeepSeek update `26fdbac` reviewed by both; historical provider-label finding corrected explicitly. No fixture results are represented as paid-provider evaluation.

## Remaining delivery requirements

Configure the DeepSeek key locally, run bounded genuine provider examples through the normal reservation/worker path, inspect measured usage and manually assess claim support/abstention. Record actual outcomes and finish GitHub review/CI before merging or closing issue #7. S07–S13, Gmail, hosted demo and project completion remain outstanding.
