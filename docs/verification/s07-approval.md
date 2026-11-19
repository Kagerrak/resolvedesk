# S07 — Exact human approval and simulated delivery

Verified locally 19 November 2026. Issue #8; implementation follows delivered S06 (PR #21, merge c50d3ad). S07 GitHub delivery remains pending final CI/review.

## Persisted behavior

An Agent/Admin prepares an immutable review of the latest nonempty saved draft, exact action differences, recipient, ticket revision, conversation digest and full published-source snapshot. Explicit approval rechecks that basis and current permissions. Cited sources must remain published and available. Uncited manual drafts require acknowledgement; citation retention does not establish edited-claim support.

Approval, unique simulated delivery intent/receipt, immutable conversation message, approved ticket changes and audit events commit in one PostgreSQL transaction. Concurrent/repeated submission of the same review reuses its receipt. A second review cannot record the same draft revision again. Changed wording, conversation, ticket or publication invalidates the review. Simulated delivery only accepts active synthetic workspaces and contains no email transport. Separate explicit ticket-change commands persist authorization; the UI confirms exact differences first. Tags are normalized and bounded.

The source publication/approval boundary shares a workspace advisory lock, including publication of newly created documents. Composite foreign keys enforce ownership of reviews, drafts and receipts. Downgrade refuses to discard a nonempty authorization ledger.

## Actual verification

- `uv run python -m scenarios.s07`: **21 genuine HTTP/PostgreSQL assertions passed** against the running application. Covers exact wording, normalized actions, no mutation on review, uncited acknowledgement, cross-workspace/Viewer denial, stale edits/conversation/revision/publication/archive, concurrent double-submit, replay after lost response, one durable receipt/message, manual-command authorization, synthetic-only restriction and expiry. Own synthetic records cleaned afterward. Requests paced to respect real sign-in limits.
- Fresh disposable PostgreSQL: upgrade head → downgrade s06_deepseek → upgrade head passed. No production database or retained authorization history was removed.
- Ruff/Pyright, ESLint/TypeScript and production build passed locally. Web production was stopped for every build and restarted afterward.
- Ego-browser: inspect exact cited reply/action review; open authorized source within review; mutate saved draft concurrently through genuine HTTP and observe stale rejection; close review, load latest without discarding local edits, compare saved draft and review again. Keyboard focus starts at review heading, Escape returns to trigger. A breakpoint transition initially hid a nested modal; moving it to the document portal fixed the issue. Final checks confirmed visible dialog and no page/dialog horizontal overflow at 360, 390, 768, 1280 and 1440px in both themes.
- Ego-browser genuine offline condition: approval fails clearly while retaining the same review; restore connection and retry records one labeled simulated reply and the approved high priority/follow-up tag. No email or AI call occurred. The browser used an existing synthetic S06 live draft; S07 made no additional provider requests.

## Independent review

Separate fresh-context Spec and Standards reviewers checked c50d3ad…30e2640. Spec: no material findings. Standards: no documented breaches; one low-priority duplicated snapshot-lock policy was extracted to a shared module. Final recovery/portal changes are queued for reviewer refresh; final CI and delivery remain pending.

## Evidence and limitations

- [Light desktop review](images/s07-review-desktop.png)
- [Dark mobile review](images/s07-review-mobile.png)
- [Recorded mobile workflow](images/s07-recorded-mobile.png)

No real Gmail delivery, hosted demo, complete S11 evaluation or native 200% zoom verification is claimed. Public generation remains fixture-only. S08–S13 remain unfinished.
