# ResolveDesk session handoff

Updated 18 November 2026.

## Active work and branch safety

Functional checkout: `/Users/rommelclarino/projects/resolvedesk-s01`, branch `feat/s06-drafting`. Original `/Users/rommelclarino/projects/resolvedesk` remains on `feat/ui-direction-prototypes` with its pre-existing screenshot changes and generated `apps/web/AGENTS.md`; do not overwrite or merge that prototype branch wholesale.

S01 PR #16 merged as `9427fec425c34cd65230c88863ac027ebea0502f`; issue #2 closed. Command Bright D adopted with real API data, light theme, mobile/keyboard flows. CI run 43829740801 passed.

S02 PR #17 merged as `7023c1a`; issue #3 closed; CI run 43998758871 passed. Its 29 API assertions and browser/review evidence are in `docs/verification/s02-manual-handling.md`.

S03 delivered: PR #18 merged as `6b3ad719`, issue #4 closed; CI 44242453555 passed. Implemented and verified: private text source storage, durable fixture indexing, section inspection, Admin publish/archive, safe retry and member visibility. Commits `7c208b0`, `3d8526a`. 25 real HTTP/PostgreSQL/worker assertions, browser journey and independent review pass. See `docs/verification/s03-knowledge.md`. S04 PR #19 merged as `fec794bd`, issue #5 closed, CI 44243139958 passed all 99 S01–S04 assertions. S05 is subsequently delivered below. User approved a local-only Admin setup command; README documents it. No live staff auth or public uploads enabled.

## Required reading and decisions

Read AGENTS.md and nested instructions, .impeccable.md, implementation-plan.md, design-system.md, GLOSSARY.md, delivery-status.md and execution-decisions.md. No TDD, test-first, unit tests, unit scaffolding or mocked units labeled integration. Implement first, then real HTTP/PostgreSQL, ego-browser, AI evaluations and static checks. Use feat/ or fix/ branches. Preserve unrelated work; no secrets or real mailbox data in Git.

Approved: Better Auth, MIT, public Kagerrak/resolvedesk GitHub Issues, S01–S13, Command Bright D, infrastructure ≤ USD25/month and separate USD20/month demo AI cap. No paid resources provisioned; verify current aggregate cost before provisioning. Do not repeat settled decisions. Ask unresolved choices interactively with a recommendation after inspecting available facts.

Matt Pocock upstream rechecked unchanged at `5863806dd4e15c63174bee4e7515a4256792ecfa`; code-review/pr local hashes match recorded versions. Ego-browser installed guide 2.2.1. Skills/customizations preserved; TDD excluded.

## Local operation and limitations

README startup and scenario instructions apply. Existing ignored environment files were safely copied to functional checkout. Local PostgreSQL container remains `resolvedesk-postgres-1`, port55432. Inspect and reuse project-owned web/API processes on3000/8000; never build over a running Next production process (restart around builds). Scenario suites require spacing for real Better Auth rate limits.

Only synthetic data is used. Temporary second QA workspace was removed. Browser sessions may expire; create fresh sessions through entry. Viewer QA membership may remain on the last synthetic session; a new session has Agent role.

S06–S13 remain unfinished. No public hosted demo, AI quality evaluation or real Gmail verification exists. Native 200% browser zoom remains unverified. Public cleanup/abuse limits, live staff auth, OAuth/provider account setup, safe delivery and budget enforcement must still be delivered. Do not call the project complete.

## S04 delivered

Implementation 630a4cf, long-text/browser evidence fd28e0d. 22 actual HTTP/PostgreSQL/PDF-subprocess assertions and S03 regression 25 assertions passed. Static checks/build pass; independent Spec/Standards review clear. See docs/verification/s04-pdf-knowledge.md. Original downloads are authenticated inert attachments; page references persist. Linux enforces an additional 512 MiB cap; macOS has CPU/wall/parser limits. No OCR/provider calls.

User approved the temporary development-only picomatch advisory exception; scripts/audit-dependencies.mjs expires it on 2 December 2026, and still blocks production and other moderate-or-higher advisories. Production audit clean. S03 remediation worktree exists at /Users/rommelclarino/projects/resolvedesk-s03; original prototype checkout remains untouched.

S04 delivery: https://github.com/Kagerrak/resolvedesk/pull/19; CI https://github.com/Kagerrak/resolvedesk/actions/runs/44243139958. S05 delivered via PR #20 merged ea41f16; issue #6 closed. CI 44307545659 passed all 129 S01–S05 assertions, fresh migrations/static/build. Next S06 generation and revision; retain explicit fixture mode and no paid provider calls before usage controls.

## S05 implementation update

S05 behavior implemented in `608f68f`, review fixes `428fa1c`, extended integration checks `8db7cf2`. Native pgvector exact cosine retrieval with persisted ranking/source-version provenance, authorized citation passages/PDF pages and mobile panel navigation. 30 real HTTP/PostgreSQL assertions passed; browser, static/build and independent Spec/Standards review evidence in `docs/verification/s05-retrieval.md`. Delivered: PR #20 merged `ea41f167f935d25fc6de787d284b732c4ba30d03`, issue #6 closed, CI https://github.com/Kagerrak/resolvedesk/actions/runs/44307545659 passed all 129 assertions. No provider calls. Local API/web restarted from functional checkout after safe builds; no background worker running.


## S06 active — not delivered

Branch `feat/s06-drafting` starts from merged S05. Implemented durable fixture generation, saved edits/citations, escalation, cancellation/staleness, strict provider validation and atomic conservative allowances. User selected DeepSeek for now, superseding OpenAI generation. Public API stays fixture-only. `DEEPSEEK_API_KEY` is absent locally; user was asked to configure it in ignored apps/api/.env or give its storage location. Never paste/read keys into chat/tool output. LIVE_AI_ENABLED defaults false; no paid requests made.

24 actual HTTP/PostgreSQL/worker assertions and 13 explicit local HTTP provider-contract fixtures pass; these are not live AI quality. Browser composer/source/edit/resume/real-connection-failure recovery passed; both themes/five widths no overflow. Fresh migration upgrade/downgrade/upgrade passed. Independent review findings fixed; see docs/verification/s06-drafting.md and docs/planning/s06-provider.md. Live DeepSeek examples/accounting/quality and final CI/GitHub delivery remain pending. Do not close #7 or promote S07 yet.

Inspect and reuse project processes on 3000/8000 before changing them; stop web production before builds. No generation or knowledge background worker is running (scenario/browser jobs were processed with --once). Key configuration alone does not enable paid calls. The local-only CLI is documented in README; enable it only for bounded verified usage. Preserve original prototype checkout.

S06 draft PR: https://github.com/Kagerrak/resolvedesk/pull/21. Expanded CI first run: https://github.com/Kagerrak/resolvedesk/actions/runs/44313099286 (superseded by final tracking push; inspect latest head check). Final local build/audit/static checks pass. Branch remains clean and pushed. Do not merge draft PR or close #7 until live DeepSeek verification and manual claim-support/abstention review are recorded.
