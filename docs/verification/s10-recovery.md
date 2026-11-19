# S10 — Independent indexing/source recovery

19 November 2026. Part of issue #11, based on delivered S07 merge f354d80. This delivers the explicitly independent indexing/source and simulated-operation Activity scope. Gmail connector health, sync recovery, real delivery retry/reconciliation and uncertain-delivery recovery remain gated by S08/S09 and are **not delivered**. Issue #11 must remain open for those cases.

## Persisted behavior

Activity reads scoped PostgreSQL generation, authorization and indexing records with filters and bounded pagination. It does not return customer bodies, source passages, provider responses or credentials. Source operations are Admin-only, including unpublished-source metadata; other members can inspect permitted ticket operations. Simulated reply records remain labeled as having no email delivery.

New indexing transitions record queue, start, completion/failure, retry and attempt-cap events in the same transactions as the corresponding effects. Publication/archive/deletion record content-free transitions. Existing operations have no invented backfilled history. Technical correlation and lease details are secondary disclosure.

Only an Admin may retry indexing. A current revision and failed/expired operation are required, attempts remain bounded at three, active locks cannot be stolen and recovery invalidates old worker tokens. Worker restart on expired durable state creates one set of indexed effects. Activity never retries paid generation or delivery.

Source deletion permanently clears uploaded bytes/text, filename/hash and indexed passages/vectors. It retains a content-free tombstone and operational events, fences in-flight indexing and revokes source navigation. Archiving/deletion invalidates dependent reply reviews. Saved reply wording and already approved conversation messages remain business records: this does not claim erasure of every source quotation from authored replies. Define production retention before live deployment; no real mailbox data is used here.

## Verification

- `uv run python -m scenarios.s10`: 29 genuine HTTP/PostgreSQL/worker assertions passed on the final implementation, including the explicit queue transition and queued-generation rejection after source deletion. A prior rerun after browser traffic stopped on a confirmed authentication-limit 503; the isolated rerun passed; the final deletion-edge extension passed all 29. Covers parser failure, real persisted history, Admin/Viewer/isolation, concurrent retry, three-attempt limits, expired versus active locks, worker restart/deduplication, real fixture retrieval/generation, stale approval/citation revocation, deletion of text/chunks/PDF bytes, tombstones and pagination. Interrupted-worker state is deliberately seeded in PostgreSQL; the actual unmocked worker then resumes it. This is not a claim that a process was killed mid-parse.
- Fresh disposable PostgreSQL upgrade → downgrade s07_approval → upgrade passed. Static checks and production build passed. Web production was stopped before rebuilding and restarted afterward.
- Ego-browser: actual heading-only upload fails in the real parser; open Activity, inspect history, retry once, run worker and observe attempt two. Genuine offline condition fails recovery clearly; restore network, refresh authoritative state, then retry safely. Source inspection opens the exact document; deletion cancellation retains it, confirmation removes its download/content and Activity shows a tombstone. Type/state filters include a genuine empty state. Keyboard Enter opens an operation and focuses its detail heading. Activity-to-ticket links open the exact older ticket with mobile conversation visible. Five widths (360/390/768/1280/1440) in both themes show no horizontal overflow.
- Deleted retrieval results retain an explicit changed/deleted signal from their persisted source versions, rather than masquerading as genuine empty evidence. Queued generation rejects that stale basis before provider dispatch and preserves the saved draft. The mobile browser warning was verified after real upload/index/publish/retrieve/delete.
- No additional paid provider or email requests during S10. Fixture vectors/generation remain explicit.

## Review and delivery

Fresh Spec/Standards review of f354d80…a35192f: Spec clear within the explicit independent scope. Standards found technical recovery jargon in primary copy; corrected to plain language and moved lease metadata into technical disclosure. Both final reviewer refreshes through 5a25a4d are clear. Final CI/GitHub delivery pending.

Evidence: [light desktop](images/s10-activity-desktop.png), [dark mobile](images/s10-activity-mobile.png), [deleted evidence warning](images/s10-deleted-evidence-mobile.png). No native 200% zoom or unattended CI browser coverage is claimed. S08/S09, remaining S10 Gmail cases, S11–S13 and hosting remain unfinished.
