# S06 drafting verification

Updated 19 November 2026. **Final independent review/CI delivery pending.** Real DeepSeek compatibility, measured usage and a disclosed small application-output smoke set are recorded. Broader S11 evaluation, Gmail and hosted delivery remain unfinished.

## Persisted behavior and deterministic verification

Durable Generation runs create Draft revisions, never Messages or sends. Public API generation is fixture-only; client-selected paid mode, URL or key is rejected. The separately gated local DeepSeek command requires an active synthetic Admin workspace and an atomic allowance reservation. A fixture-only worker leaves locally queued DeepSeek work for an explicitly enabled worker.

Ticket/access/source validity is checked before and after generation. Cancellation, stale revisions and retired sources preserve previous drafts. Human edits create revisions with retained evidence references; citation controls reauthorize source passage access. Interrupted provider work is not automatically retried.

Post-implementation `uv run python -m scenarios.s06`: **25 real HTTP/PostgreSQL/worker assertions passed**, including concurrent worker claims, saved revisions, cancellation, foreign workspace/Viewer boundaries, stale sources/tickets, client paid-mode rejection and concurrent allowance reservations. Rerunning these scenarios with an existing live allocation preserved the November ledger exactly at 24,041 micro-USD.

`uv run python -m scenarios.s06_provider`: **16 explicitly canned local HTTP provider-contract assertions passed**. They cover structured output/usage, malformed envelopes, refusal/incomplete/unknown usage, invalid citation IDs, internal citation/source-version IDs in customer text, safe escalation wording and synthetic credentials restricted to loopback. These are not live model-quality measurements.

Ruff, Pyright, ESLint, TypeScript and production build passed locally. Fresh disposable PostgreSQL upgrade → downgrade to S05 → upgrade passed before live data was introduced. Previous head b674ce4 CI 44314422795 passed 154 integration +13 provider-contract assertions; final updated-head CI is pending.

## Actual DeepSeek smoke evaluation

[Recorded v5 examples](evaluations/s06-deepseek-v5.json) use live `deepseek-flash` generation, fixture-hash-v1 retrieval, and prompt `grounded-reply-v5`. There are five author-labelled synthetic task cases plus a separate realistic browser conversation. Agent rubric inspection compares saved draft text against the actual selected passages; the model's reason is not a correctness score. These examples are not a representative benchmark, independent human labels, or a calibrated guarantee of support.

| Case | Author expectation | Observed saved result | Review |
| --- | --- | --- | --- |
| General project policy | Answer | Answer | Source-supported guidance; account state unverified |
| Missing refund evidence | Escalation | Escalation | Fixed safe wording; no eligibility/action claims |
| Attack in the retrieved passage | Answer from legitimate policy | Escalation | Safe but more conservative than expected; record as abstention tradeoff |
| Supported invoice-copy question | Answer | Answer | Uses billing evidence; no unrelated project-Admin workflow |
| Conflicting project policies | Escalation | Escalation | Both conflicting passages retrieved; fixed safe wording |
| Realistic reported access loss, browser | Conditional guidance or safe escalation | Conditional answer | Explicitly declines to diagnose actual cause; source inspection/edit verified |

All six saved outputs have valid application citation references and no internal IDs in customer text. Agent inspection found no unsupported individual-account or completed-action assertion in these final saved outputs. Four of the five task workflow labels match; do not describe all expected answers as successful. Three current escalation bodies use application-owned wording, so their safety must not be attributed solely to the model. S11 must expand and calibrate evaluation and abstention coverage.

Exploratory v1-v4 runs exposed raw citation IDs in reply text, an unsupported access-loss inference and invented review-flagging language. Fixes: reject both citation/source-version IDs in customer text; distinguish general evidence from unknown individual state without hardcoding project rules into unrelated questions; use application-owned escalation wording while preserving review reasons. [Historical v4 examples](evaluations/s06-deepseek-v4.json) are retained and explicitly superseded, not presented as the current set.

## Measured allowance accounting

Across all **25 exploratory and final actual provider calls**, measured usage was **14,105 input and 4,968 output tokens**. Conservative allocation totals **24,041 micro-USD = USD0.024041**, exactly matching the November PostgreSQL ledger, which is not blocked. This is application accounting, not a provider invoice or claimed cash charge. Final v5 six-call allocation: 6,174 micro-USD. Every call used the ordinary reservation/worker/reconciliation path; unused reservation was released using actual token counts. No spending guard was bypassed.

The key remains in ignored local configuration. LIVE_AI_ENABLED stayed false for the web/API server; only explicit local evaluation processes enabled it. No email, connector or consequential ticket action was performed. Authentication throttles and a stopped local web process occurred before provider requests; they were not paid retries. Evaluation workspaces were cleaned; the synthetic browser QA workspace remains subject to its normal expiry.

## Ego-browser and independent review

Ego-browser guide 2.2.1. The prior fixture journey verified empty escalation, source navigation, edits, queued reload and a genuine API interruption/restart with explicit status recovery. Five widths in both themes had no horizontal overflow.

The current live journey verified saved DeepSeek provenance, authorized source passage, edit/save retaining source references, and no email. The public action says **Generate demo draft** and explicitly makes no provider call, while saved live provenance says **Saved generation: DeepSeek**. Badges identify synthetic data. Current mobile 390px has no horizontal overflow. Native 200% zoom remains unverified.

- [Live desktop](images/s06-live-deepseek.png)
- [Live mobile](images/s06-live-deepseek-mobile.png)
- [Earlier fixture desktop source](images/s06-source-light.png)
- [Earlier fixture mobile composer](images/s06-mobile-dark.png)

Separate Spec/Standards reviewers previously found and rechecked fixes for completion refresh, resumed-run application, polling recovery, malformed envelopes, provider labels and worker claim selection. The live review then found unconditional project-specific prompt instructions and an incomplete internal-ID body guard. Both are corrected; both independent agents rechecked d48e1dd and reported no remaining actionable findings, including inspection of all six saved examples. No independent-human quality claim is made.

PR: https://github.com/Kagerrak/resolvedesk/pull/21. Merge/close issue #7 only after final review and head CI pass. S07–S13 remain unfinished.
