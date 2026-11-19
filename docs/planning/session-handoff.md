# ResolveDesk session handoff

Updated 18 November 2026.

## Active work and branch safety

Functional checkout: `/Users/rommelclarino/projects/resolvedesk-s01`, branch `feat/s10-recovery`. Original `/Users/rommelclarino/projects/resolvedesk` remains on `feat/ui-direction-prototypes` with its pre-existing screenshot changes and generated `apps/web/AGENTS.md`; do not overwrite or merge that prototype branch wholesale.

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

S06–S13 remain unfinished. No public hosted demo, completed S11 quality evaluation or real Gmail verification exists. Initial live DeepSeek smoke examples are recorded below. Native 200% browser zoom remains unverified. Public cleanup/abuse limits, live staff auth, OAuth/provider account setup, safe delivery and budget enforcement must still be delivered. Do not call the project complete.

## S04 delivered

Implementation 630a4cf, long-text/browser evidence fd28e0d. 22 actual HTTP/PostgreSQL/PDF-subprocess assertions and S03 regression 25 assertions passed. Static checks/build pass; independent Spec/Standards review clear. See docs/verification/s04-pdf-knowledge.md. Original downloads are authenticated inert attachments; page references persist. Linux enforces an additional 512 MiB cap; macOS has CPU/wall/parser limits. No OCR/provider calls.

User approved the temporary development-only picomatch advisory exception; scripts/audit-dependencies.mjs expires it on 2 December 2026, and still blocks production and other moderate-or-higher advisories. Production audit clean. S03 remediation worktree exists at /Users/rommelclarino/projects/resolvedesk-s03; original prototype checkout remains untouched.

S04 delivery: https://github.com/Kagerrak/resolvedesk/pull/19; CI https://github.com/Kagerrak/resolvedesk/actions/runs/44243139958. S05 delivered via PR #20 merged ea41f16; issue #6 closed. CI 44307545659 passed all 129 S01–S05 assertions, fresh migrations/static/build. Next S06 generation and revision; retain explicit fixture mode and no paid provider calls before usage controls.

## S05 implementation update

S05 behavior implemented in `608f68f`, review fixes `428fa1c`, extended integration checks `8db7cf2`. Native pgvector exact cosine retrieval with persisted ranking/source-version provenance, authorized citation passages/PDF pages and mobile panel navigation. 30 real HTTP/PostgreSQL assertions passed; browser, static/build and independent Spec/Standards review evidence in `docs/verification/s05-retrieval.md`. Delivered: PR #20 merged `ea41f167f935d25fc6de787d284b732c4ba30d03`, issue #6 closed, CI https://github.com/Kagerrak/resolvedesk/actions/runs/44307545659 passed all 129 assertions. No provider calls. Local API/web restarted from functional checkout after safe builds; no background worker running.


## S06 final verification — delivered

Updated 19 November 2026. Branch `feat/s06-drafting`, draft PR https://github.com/Kagerrak/resolvedesk/pull/21. User configured DEEPSEEK_API_KEY locally; never output/copy it into chat or Git. LIVE_AI_ENABLED remains false in the server environment. Paid calls were enabled only in local evaluation processes and public generation remains fixture-only.

Previous head b674ce4 passed CI 44314422795: 154 real integration assertions +13 explicitly canned local HTTP provider-contract checks. Live review then found internal citation IDs in body text, an unsupported access-loss inference, and invented review-flagging language. Current changes: prompt grounded-reply-v5, application-owned escalation wording, internal-ID body rejection, clear saved-provider/public-demo-action labels; 16 provider-contract checks pass. Final head ad3ad76 passed CI 44472186034 and independent review; PR #21 merged c50d3ad. See docs/verification/s06-drafting.md and evaluations/s06-deepseek-v5.json.

Twenty-five exploratory/final actual DeepSeek calls returned measured usage totaling 14,105 input +4,968 output tokens. Conservative allocation USD0.024041 exactly matches November PostgreSQL ledger; not a provider invoice. Current smoke set: five author-labelled task cases plus a separate realistic browser case. Three replies are application-normalized escalations; three provide conditional supported guidance. One task case conservatively escalated instead of its expected answer (four of five workflow labels match); keep this limitation explicit. Agent rubric review is disclosed; these are not an independent human-labelled benchmark. Broader S11 quality work remains unfinished.

Browser verified live provider provenance/source opening/edit+save and mobile no overflow; prior fixture/resume/connection-recovery checks remain valid. Existing web/API were inspected and restarted after overnight shutdown, and the production web was stopped before its final build. No background generation/knowledge worker is running. Use normal --once or worker commands as needed; default fixture-only worker leaves local paid work for an explicitly enabled worker. Live evaluation workspaces were cleaned; browser QA workspace remains synthetic and expires normally.

PR #21 delivered and issue #7 closed; S07 is active. Keep S07–S13, hosted demo and Gmail verification unfinished. Preserve original prototype checkout and pending files.


## S06 delivered / S07 active — 19 November 2026

S06 PR #21 merged `c50d3ade794a8621879cea4facadc963d4b2afba`; issue #7 closed. Final CI [44472186034](https://github.com/Kagerrak/resolvedesk/actions/runs/44472186034) passed 154 real integration assertions and 16 explicitly canned local HTTP provider-contract checks, migrations/static/build/audit. Independent final Spec/Standards review clear. Live smoke limitations and USD0.024041 conservative measured allocation are preserved in docs/verification/s06-drafting.md. Public generation remains fixture-only. S07 issue #8 is unblocked; active branch `feat/s07-approval`. S07–S13, hosting and Gmail remain unfinished.


## S07 implementation / verification in progress

Branch feat/s07-approval. Exact persisted reviews, human authorization, synthetic transactional delivery receipts/messages, tags and accessible review UI implemented. Local 21 genuine integration assertions, fresh migration round trip, static/build and browser stale/offline/mobile journeys passed. Separate Spec/Standards review found no blocker; shared lock suggestion fixed. Final reviewer refresh and GitHub CI/delivery pending. See docs/verification/s07-approval.md. Gmail setup question is pending interactively; do not claim S08 live verification. Public generation remains fixture-only; no additional paid AI calls during S07.


## Current frontier — 19 November 2026

S07 delivered via PR #22, merge f354d801ab8f5a3094edc7ab9f7598a94dea78ce; issue #8 closed. CI 44475535950 passed 175 real S01–S07 assertions +16 distinctly canned local provider-contract checks, static/build/migration/audit. Final Spec/Standards refreshes clear; report docs/verification/s07-approval.md. No S07 paid provider calls.

S08 OAuth credentials and encryption key are absent. Interactive question pending: help configure a dedicated synthetic test mailbox and Google OAuth client / already configured / defer real verification. Do not infer an answer. Gmail has not been accessed. Prep notes docs/planning/s08-connector-preparation.md. Issue #9 remains blocked/needs-info. S09 remains blocked by S08. S10 indexing/simulated recovery is explicitly independently unblocked per issue #11; now active on feat/s10-recovery. S11 issue #12 is also unblocked/ready-for-agent but not implemented. S10 Gmail recovery cases remain gated by S08/S09. Never claim project complete.

API production process currently runs from this functional checkout; web was safely stopped/rebuilt/restarted for final S07 changes. Inspect current ports/processes before restarting. No background workers run. Ego TaskSpace 27 was finished with keep=[] after verification/research. Use a new space only if it no longer exists. Original prototype checkout remains untouched. The local .env key remains ignored and LIVE_AI_ENABLED=false. Audit passed; latest observed picomatch remains4.0.7; exception unchanged.
