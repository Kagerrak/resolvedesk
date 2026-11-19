# S06 drafting verification — work in progress

Updated 19 November 2026. **Final review/CI delivery pending.** Live DeepSeek compatibility, measured usage accounting and the disclosed five-example application-output smoke review are recorded below. Broader S11 quality evaluation remains unfinished.

## Implemented and verified locally

- Durable generation runs create Draft revisions, never Messages, approvals or sends. Public API is fixture-only. Sources/access/ticket revision are checked before and after generation. Stale outcomes are discarded, cancellation preserves previous drafts, and interrupted provider jobs are not retried automatically.
- Human edits create another revision retaining generation/citation provenance. Composer citation controls open authenticated exact source passages. Provider responses are validated for envelope, schema, authorized citation IDs and required evidence.
- Local-only DeepSeek path requires explicit LIVE_AI_ENABLED, DEEPSEEK_API_KEY, loopback endpoints and an active synthetic Admin workspace. Conservative PostgreSQL reservations serialize monthly/session spending before provider calls; token usage releases unused reservations. Unknown acceptance retains full allocation. Pricing details and official sources: [provider notes](../planning/s06-provider.md).

Post-implementation `uv run python -m scenarios.s06`: **25 real HTTP/PostgreSQL/worker assertions passed**, covering fixture/escalation drafts, concurrent worker claims, idempotent queued requests, cancellation, editing/provenance, stale ticket/source rejection, foreign workspace and Viewer rules, request/month/session accounting and concurrent monthly reservations. Uses actual sessions and PostgreSQL; scenario-owned data is deleted.

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

## Delivery requirements

The locally configured key, bounded live examples, measured usage and agent rubric review are now recorded. Finish independent review and final-head CI before merging or closing issue #7. S07–S13, Gmail, hosted demo and project completion remain outstanding.

Draft PR: https://github.com/Kagerrak/resolvedesk/pull/21. Final static/build/dependency audit passed locally after the review fixes. Expanded head CI covers S01–S06 and the labeled local provider contract; live DeepSeek evaluation is excluded without credentials.

Fixture-only worker selection also verified: a synthetic locally queued DeepSeek record stays queued with zero reservation while live mode is disabled. The local live CLI selects its exact run ID when enabled, so unrelated fixture work cannot consume its one-shot execution.

## Live verification completed 19 November 2026

The key was configured locally without entering chat or Git. Live calls were enabled only in the local evaluation process; the server's default LIVE_AI_ENABLED remains false and public requests remain fixture-only.

[Final recorded examples](evaluations/s06-deepseek-v4.json) contain **five actual DeepSeek saved-draft smoke examples** under `grounded-reply-v4`: supported policy, no evidence, an instruction attack inside the selected passage, conflicting policy passages, and the realistic seeded access-loss conversation. All five have application-valid citation IDs and expected answer/escalation outcomes. Agent rubric inspection found no unsupported account diagnosis or completed-action claim in these final saved drafts. This is a small disclosed agent-reviewed smoke set, not a representative benchmark or independently human-labelled quality result. S11 remains unfinished.

Live review exposed defects in earlier prompts: internal citation UUIDs in reply text, an unwarranted inference about the customer's actual access, and claims that a review had already been flagged. The final application rejects internal citation IDs in customer text, strengthens conditional account guidance, and supplies fixed escalation wording while retaining source/conflict reasons for the Agent. Two of the five final bodies use this application-owned escalation wording; their correctness must not be attributed solely to the model. Earlier exploratory outputs are excluded from the final five-case rubric.

Measured usage across **19 exploratory and final live calls**: 10,387 input tokens, 3,740 output tokens; conservative allocation **17,867 micro-USD = USD0.017867**. The PostgreSQL November ledger exactly matches these per-run allocations and is not blocked. This is conservative application accounting, not a provider invoice; no billed-cost total is claimed. Final five-call allocation: 5,466 micro-USD. Unused reservation was released from measured token counts on the normal worker path. No spending controls were bypassed.

Ego-browser verified the actual live draft after the local Admin command: **Saved generation: DeepSeek**, authorized source passage, subsequent edit/save with retained references, and no email delivery. The action remains **Generate demo draft** with explicit no-provider-call guidance, separating the saved live provenance from the public action. Workspace badges now describe synthetic demo data rather than incorrectly implying all historical generations are fixtures.

- [Live desktop](images/s06-live-deepseek.png)
- [Live mobile](images/s06-live-deepseek-mobile.png)

The anonymous-session limit was respected; subsequent cases used one synthetic evaluation workspace with separate immutable ticket/message fixtures, archived old sources, and cleanup. No real customer/mailbox content was used. Live evaluation workspaces were deleted; the local browser QA workspace remains synthetic and expires normally. Native 200% zoom remains unverified.
