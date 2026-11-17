# ResolveDesk session handoff

Updated 17 November 2026.

## Active work and branch safety

Functional checkout: `/Users/rommelclarino/projects/resolvedesk-s01`, branch `feat/s02-inbox`. Original `/Users/rommelclarino/projects/resolvedesk` remains on `feat/ui-direction-prototypes` with its pre-existing screenshot changes and generated `apps/web/AGENTS.md`; do not overwrite or merge that prototype branch wholesale.

S01 PR #16 merged as `9427fec425c34cd65230c88863ac027ebea0502f`; issue #2 closed. Command Bright D adopted with real API data, light theme, mobile/keyboard flows. CI run 43829740801 passed.

S02 implemented and locally verified. Commits `f3103e0`, `685f4a0` contain real scoped search/filter, draft revisions, explicit assignment/priority/status/reopen, optimistic concurrency and audit history. Local 29 S02 + 23 S01 assertions pass; browser and independent reviews pass. See `docs/verification/s02-manual-handling.md`. Finish S02 GitHub delivery/CI before closing issue #3. S03 #4 is unblocked; prioritize knowledge publication next.

## Required reading and decisions

Read AGENTS.md and nested instructions, .impeccable.md, implementation-plan.md, design-system.md, GLOSSARY.md, delivery-status.md and execution-decisions.md. No TDD, test-first, unit tests, unit scaffolding or mocked units labeled integration. Implement first, then real HTTP/PostgreSQL, ego-browser, AI evaluations and static checks. Use feat/ or fix/ branches. Preserve unrelated work; no secrets or real mailbox data in Git.

Approved: Better Auth, MIT, public Kagerrak/resolvedesk GitHub Issues, S01–S13, Command Bright D, infrastructure ≤ USD25/month and separate USD20/month demo AI cap. No paid resources provisioned; verify current aggregate cost before provisioning. Do not repeat settled decisions. Ask unresolved choices interactively with a recommendation after inspecting available facts.

Matt Pocock upstream rechecked unchanged at `5863806dd4e15c63174bee4e7515a4256792ecfa`; code-review/pr local hashes match recorded versions. Ego-browser installed guide 2.2.1. Skills/customizations preserved; TDD excluded.

## Local operation and limitations

README startup and scenario instructions apply. Existing ignored environment files were safely copied to functional checkout. Local PostgreSQL container remains `resolvedesk-postgres-1`, port55432. Inspect and reuse project-owned web/API processes on3000/8000; never build over a running Next production process (restart around builds). Scenario suites require spacing for real Better Auth rate limits.

Only synthetic data is used. Temporary second QA workspace was removed. Browser sessions may expire; create fresh sessions through entry. Viewer QA membership may remain on the last synthetic session; a new session has Agent role.

S03–S13 remain unfinished. No public hosted demo, AI quality evaluation or real Gmail verification exists. Native 200% browser zoom remains unverified. Public cleanup/abuse limits, live staff auth, OAuth/provider account setup, safe delivery and budget enforcement must still be delivered. Do not call the project complete.
