# S02 manual handling verification

Completed local verification 17 November 2026, on `feat/s02-inbox` after `9427fec` (delivered S01). Implementation commits `f3103e0`, `685f4a0`.

## Persisted behavior

- New migration adds nullable workspace-member assignment, immutable draft revisions and ticket audit events.
- Search/status/assignment filters query PostgreSQL through the API; URL query persists filters across reload.
- Explicit Apply changes writes status/priority/assignment atomically with audit. Reopen changes only the saved ticket status, leaving other unapplied local fields untouched.
- Save draft creates a revision and never a Message or email. Expected ticket revision and row locks reject stale/concurrent edits. Viewer and cross-workspace mutations are rejected.

## Verification evidence

- `uv run python -m scenarios.s02`: **29 assertions passed**, genuine HTTP/Better Auth/PostgreSQL; no mocks. Includes case-insensitive/literal search, assignment filters, membership isolation, foreign assignee rejection, persisted changes and exact audit, no-op handling, immutable drafts, concurrent writers (one success/one 409), payload bounds, origin checks, explicit resolve/reopen, Viewer rejection and database revision/message counts.
- `uv run python -m scenarios.s01`: **23 assertions passed** after the change. A first immediate sequential run hit the maintained auth library's anonymous-session rate limit; rerun after its window passed succeeded. CI spaces the suites by 61 seconds, retaining production protection. Auth 429 now reports temporary unavailability rather than a false ended session.
- Web lint/types/build and Python Ruff/Pyright pass. Migration applies to the existing local PostgreSQL database.
- Ego-browser 2.2.1: save draft, explicit assignment/priority/status, reload persistence, filtered empty result and reload URL persistence, resolve/reopen, keyboard/mobile save and Back focus restoration.
- Two browser editors: stale save returns conflict and preserves local A while latest saved B is available for comparison; explicit restore takes B. Failed queue + concurrent saved D + general Retry retains local C, disables saving and requires explicit comparison (does not silently advance edit baseline).
- Deterministic delayed mutation: held the real PostgreSQL Ticket row lock for eight seconds; began save in workspace A then switched to a separate permitted synthetic workspace B. The original save committed, but no A heading appeared under B (observed DOM mutations). Temporary QA workspace removed.
- Reopen with unsaved priority `urgent` kept saved priority `high`; only subsequent Apply changed it.
- Viewer role applied in the real database: saved draft/history readable, zero text editors or save/apply/reopen controls.
- Both themes: 360, 390, 768, 1280 and 1440px show the editor without horizontal page overflow. Screenshots: `s02-desktop-dark.png`, `s02-desktop-light.png`, `s02-mobile-dark.png`.
- Independent Spec/Standards review found three substantive edge cases (late response, silently advancing edit revision, unrelated reopen changes); fixed in `685f4a0`, rechecked by reviewers and verified in browser. No remaining material findings.

Native 200% browser zoom remains unverified from S01; CSS 200% reflow previously passed. No full accessibility certification, unattended browser CI, hosted demo, live AI or Gmail claims. No paid resources provisioned, TDD or unit-test scaffolding introduced.
