# S11 quality evaluation — verification in progress

19 November 2026. Implementation first; no TDD, unit tests or mocked database. GitHub issue #12. Real Gmail remains explicitly deferred; this report does not establish Gmail delivery or hosted-demo readiness.

## Behavior and provenance

Durable workspace-scoped EvaluationRun/Case/Review records, dataset and source SHA-256 hashes, ticket snapshots, ranked source labels, retriever parameters, model/prompt version, exact output hashes, timing and allocation. The local worker parses/indexes actual PostgreSQL sources, publishes the approved corpus, keeps a retired invitation article archived, and temporarily publishes a conflicting refund policy only for its two cases. A deliberately similar private source is published in a second workspace; the same actor belongs to both, so membership alone cannot bypass selected-workspace filtering. Temporary private/conflicting sources are cleaned on terminal states.

The frozen authored dataset has 24 articles and 50 cases, 12 tuning / 38 held out. Expected labels enter scoring only. Baseline tuning was completed before the lexical candidate was implemented. Candidate BM25 parameters were committed in 5b6ee51 before any held-out evaluation; no held-out label or ranking was changed afterward. Default ticket retrieval remains exact pgvector cosine with explicitly synthetic vectors. The lexical candidate is an evaluation method over already-authorized PostgreSQL chunks. Fixture extracts are simulations saved as evaluation cases, not fifty normal draft generations. Ten predetermined held-out live cases use the normal generation queue, exact provenance, ten-generation session limit and atomic spending controls.

## Measured comparison

| Measurement | Exact cosine baseline | Fixed lexical candidate |
|---|---|---|
| Planned/completed cases |50/50|50/50|
| Expected source labels in answerable cases |38/40 (95%)|40/40 (100%)|
| Held-out expected source labels |27/29 (93.1%)|29/29 (100%)|
| Tuning expected source labels |11/11|11/11|
| Fixture workflow label match |36/50|37/50|
| Fixture emitted citation IDs valid |50/50|49/49|
| Actual DeepSeek outputs |0|10/50 cases|

Source recall counts each expected article label in planned answerable cases (36 cases,40 labels); unfinished cases contribute zero hits. Abstention cases are excluded from that recall denominator. Citation validity checks IDs against the actual retrieved authorized snapshot, not whether every claim is supported. Targets are finite-set aims, not universal guarantees. Baseline answerable misses were c20 (refund policy absent) and c31 (notification source absent). It also missed both conflicting-policy sources for abstention case c46, which is intentionally outside the answerable-recall denominator. This illustrates why recall alone cannot establish safe answer behavior. The candidate improves this frozen synthetic set; it does not establish semantic embedding quality or representative production retrieval.

The live sample uses deepseek-flash / grounded-reply-v5. All 10 calls completed with measured usage 13,567 input+2,943 output tokens. Conservative app allocation USD0.019453, not provider invoice. Ledger before USD0.024041; verified after USD0.043494. No paid request was enabled from the public API; server LIVE_AI_ENABLED remains false. Provider-processing median 1,912ms, p95 2,895ms (ten domain/worker measurements, excluding browser rendering). Candidate retrieval median 35.5ms, p95 53.0ms (50 cases).

Live structured workflow matches 7/10 authored labels. Failures are retained: c13 conservatively escalated an answerable project-access case; c43 and c48 refused private disclosure but returned structured outcome=answer where the authored label expected escalation. Three saved escalations use application-owned normalized wording; do not attribute their final wording solely to the model. All 19 emitted live citation IDs were authorized. Zero observed workspace-marker disclosures/unapproved persisted effects across 50 fixture/10 live outputs; this finite probe set is not a general safety guarantee. There are three dedicated isolation cases, two in the live sample.

## Claim-support review

The provisional rubric was recorded before live output and read against eight authored calibration illustrations. Agent-applied supplementary review compares all ten exact saved outputs with the selected source versions and customer text. It is not independent human ground truth, a provider self-score, or evidence of rater reliability. No numeric answer-quality release threshold is set. All ten exact output hashes have persisted agent_rubric annotations: seven supported answers, two safe escalations and one conservative escalation. Answer-support denominator is seven reviewed answers, not ten cases or fifty provider outputs. The supported c43/c48 refusals retain their structured-workflow mismatches. Genuine authenticated HTTP checks confirmed an idempotent repeated assessment returns the same record and a wrong output hash is rejected (409). No member/human assessment was fabricated.

## Implementation-first verification

- 35 genuine HTTP/PostgreSQL/evaluation-worker assertions passed locally: Agent/Viewer/Admin controls, cross-workspace run/case denial, request idempotency under concurrency, intent binding, paid payload rejection, default worker ignoring paid mode, explicit local gate, actual parsing/indexing/publication, no DraftRevision/quota bypass for fixture simulations, exact live-review requirement, cancellation with genuinely published conflict cleanup, expired durable-lease resume, scoped pagination/split filtering, frozen-conversation and corpus changes, preservation of unrelated sources, expiry reauthorization and no paid requests/effects in the deterministic suite.
- Fresh empty database migrated to head, downgraded S11 to S10, then upgraded to head; temporary database removed. Existing ledgers are never downgraded.
- Ruff/Pyright, web lint/type checking/production build passed. Audit passed with zero production and zero development findings; latest observed picomatch remains 4.0.7. The narrow approved advisory exception remains unchanged and expires 2 December.
- 16 separately labeled canned local HTTP provider-contract checks passed; these are not live AI quality evidence.
- Independent Spec/Standards reviews through 34ee8ea are clear after fixing split pagination, exact approved-value effect comparison and terminal conflict retirement. Initial concurrency concern was retracted because require_admin already holds the exclusive workspace snapshot advisory lock.
- Ego-browser verified initial empty state, queue via the actual UI, saved live/fixture comparison, exact source passage opening, keyboard Enter/focus on case heading, page3→tuning pagination reset, unsaved-note discard cancellation, real offline failure and authoritative recovery. Expanded source versions/hashes initially overflowed mobile; wrapping was fixed and all360/390/768/1280/1440 widths in both themes now fit the actual client viewport. Screenshots in images/s11-quality-{dark,light,mobile}.png were visually inspected. Final browser refresh also confirmed Back-to-cases focus return and truthful unavailable-state wording during offline recovery. Ego space30 finished with keep=[]. CI/GitHub delivery remains in progress. An assessment API batch encountered the real sign-in rate limit after four writes; those four reviews remained saved. Respect the existing one-minute limit before resuming rather than disabling it.

Artifacts: evaluations/s11/tuning-baseline.json, full-baseline.json; candidate-live.json with all fifty cases and ten exact-output agent annotations. Dataset: apps/api/resolvedesk/datasets/meridian-support-2026-11-19-v1.json. Rubric: docs/planning/s11-review-rubric.md.
