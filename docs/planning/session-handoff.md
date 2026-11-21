# ResolveDesk session handoff

Updated 19 November 2026.

## Active work and branch safety

Functional checkout: `/Users/rommelclarino/projects/resolvedesk-s01`, branch `feat/s12-demo`. Original `/Users/rommelclarino/projects/resolvedesk` remains on `feat/ui-direction-prototypes` with its pre-existing screenshot changes and generated `apps/web/AGENTS.md`; do not overwrite or merge that prototype branch wholesale.

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

S08/S09, remaining S10 Gmail cases and S11–S13 delivery remain unfinished. No public hosted demo or real Gmail verification exists. S11 measured results are recorded below; GitHub delivery is pending. Initial live DeepSeek smoke examples are recorded below. Native 200% browser zoom remains unverified. Public cleanup/abuse limits, live staff auth, OAuth/provider account setup, safe delivery and budget enforcement must still be delivered. Do not call the project complete.

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


## S10 independent implementation — verification/delivery pending

Behavior a35192f plus pending review/copy/queue-history refinements. Scoped Activity, content-free indexing/source history, bounded Admin retry with expired-worker fencing, source content deletion/tombstones, exact source/ticket navigation. 27 real integration assertions passed initially; final queue-event rerun underway. Fresh migration/static/build and ego-browser failure/offline/retry/delete/keyboard/mobile flows passed. Review found only primary-copy jargon, fixed; final refresh and CI pending. See docs/verification/s10-recovery.md. Keep issue #11 open for Gmail recovery after independent delivery; add remaining native blockers #9/#10 and remove ready-for-agent then. S11 remains independently ready. No S10 paid AI calls.


19 November steering: user explicitly chose “Defer real Gmail verification for now.” Do not repeat OAuth/mailbox setup questions. No Gmail connection or live verification exists. Independent S10 final 27-scenario rerun passed after respecting sign-in spacing; both final reviews through bf51a6d clear. S10 partial PR/CI delivery next, then independently unblocked S11.


S10 final deletion review found that cascading deleted passages could make old retrieval appear empty. Fixed in 5a25a4d: source-version comparison exposes sources_changed, generation rejects stale deleted evidence before any provider dispatch, and Evidence shows a changed/deleted warning. Final29 real assertions passed; both reviewer refreshes clear. Browser verified the new warning after an actual source lifecycle. PR #23 final-head CI pending (old-head run44522227577 cancelled after this material fix). S08/S09 live verification remains explicitly deferred.


## Current S11 frontier

Independent S10 PR #23 merged fb059bf368f87086b74bb26db4375fa0db3b1670; CI44523451098 passed204 genuine integration assertions +16 separately canned provider-contract checks, static/migration/build/audit. Both final reviews through5a25a4d clear. Issue #11 remains open/blocked; native remaining dependencies #9/#10 added. User explicitly deferred real Gmail verification; no more OAuth setup questions during this phase.

Active branch feat/s11-quality from merged main, issue #12. Dataset draft24 articles/50 tickets (12 tuning/38 held out) and rubric now present; no S11 evaluation or paid call executed. /tmp/resolvedesk-s11-plan.md has implementation preparation. Critical: GenerationRun quota counts ALL modes (10/workspace), so fixture evaluations must be separate EvaluationCase simulations through real scoped context/provider validation, not50 normal DraftGeneration runs or a hidden cap bypass. At most10 actual live sample generations use normal quota/usage controls, explicit local Admin-only enablement; public evaluation stays fixture-only. Existing public paid access remains off. Budget20/month and.25/session remain unchanged.

Current API/web serve S10 final code; inspect processes before restart/build. No background worker runs. Ego space28 disappeared after user-turn/session interval; inventory confirmed absent, so fresh space29 was created for continuing verification. Fresh synthetic QA workspace096ba070-afc5-4824-9507-98ae13cbedf6, active local Admin; its published/retrieved test source was deleted to verify the stale warning. Prior expired QA workspaceea2303f7-ff7c-4eb8-af3f-128b7ec40bae is preserved. Do not touch user space0 or job-application space26. No additional paid calls during S07/S10; November conservative ledger remains S06 usage unless verified otherwise. S11 fresh evaluation should use a clean owned synthetic workspace.


## S11 implemented / final delivery pending — 19 November 2026

Branch feat/s11-quality. Behavior5b6ee51, recovery/35 actual API/PostgreSQL/worker scenarios34ee8ea. Frozen24-article/50-case dataset and fixed BM25 candidate; baseline tuning completed before candidate, candidate committed before held-out results. Full baseline38/40 answerable source labels, candidate40/40; held-out27/29→29/29. Public/default ticket retrieval remains exact fixture-vector cosine. Ten predetermined actual DeepSeek outputs completed through normal generation/quota/spend controls, all19 emitted IDs valid, structured workflow7/10 with retained c13/c43/c48 failures. Seven supported answers/two safe escalations/one conservative escalation under supplementary agent rubric; all ten exact-output reviews persisted. Not human ground truth or a numeric quality release threshold. Artifacts evaluations/s11/, report docs/verification/s11-quality.md.

S11 measured usage13,567 input+2,943 output, conservative allocation USD0.019453. Central November usage_month verified USD0.043494 (S06 prior0.024041+S11). Not provider invoice. Local ignored key unchanged, server LIVE_AI_ENABLED=false; no more S11 paid calls needed. Dedicated evaluation workspace955b2086-caa1-4f35-b5fb-488d24d22e40 holds all three runs and ten normal paid generations, expires2026-11-19T14:31:28Z. Private probe workspaces were cleaned. Do not use other sessions to bypass the ten-generation limit.

Static/build/fresh migration roundtrip and35 real scenarios pass;16 separately canned provider-contract assertions pass. Independent two-axis review clear through34ee8ea, final refresh pending current provenance/browser fixes. Actual browser queue/live comparison/source opening, split pagination, keyboard focus, unsaved-note confirmation, offline/recovery, five widths/both themes verified. Expanded hashes overflow found and fixed with wrapping. Final mobile Back-to-cases and truthful offline-state recovery passed. Ego space30 was finished with keep=[];29 no longer existed. Do not touch user0/job26. API/web safely rebuilt/restarted; inspect ports before mutations. No background workers running. Audit0 production/0 development findings, latest picomatch4.0.7, exception unchanged. Gmail remains explicitly deferred; no OAuth questions.


## Current frontier — 21 November 2026

S11 delivered: PR #24 merged822d81d33e49961bf8c24f9917b5d098d87251fb, issue #12 closed. Final CI44538711481 passed241 real integration assertions+16 explicitly canned provider-contract checks, static/migration/build/audit. Both final review refreshes through17644b2 clear. Distinct-ticket quota race fixed and verified with real9+2 concurrent fixture submissions. No additional paid calls; November allocation last verifiedUSD0.043494. AllS11sample/data/rubric limitations remain in report.

Active branch feat/s12-demo from mergedmain. User said useexisting hosting; VercelCLI28.11.0 authenticatedKagerrak, no ResolveDesk project existed in inspected account. EphemeralCLI66.2.0 supports current FastAPI/Services features; globalCLI/customizations unchanged. Read-only API requires explicit team; pending interactive choice: my-team-7e4eb888 (recommended) versus alpa-pro-team. No selection inferred, no resources provisioned. Do not repeat Gmail questions: real Gmail remains deferred. S12 issue13 stays blocked for deployment/dependency frontier; independent local public-demo controls can progress.

Official hosting docs checked19November: VercelServices beta allplans, FastAPI supported; HobbycontinuousDaemon420GB-hours/month insufficient for continuous1GiB month. Prefer on-demand fixture-only publicdemo with private APIservice and dedicated NeonFree PostgreSQL, subject to actual selected team/Marketplace plan verification beforeprovisioning. NeonpublicFree pricing lists100CU-hours/1GB/project, hard suspension atcompute/egresslimits; Marketplace plan must bechecked separately. No paidupgrade/AIpublicactivation approved by implication. Overallinfra cap25/month remains.

Prior ego space30 finished keep=[] afterS11QA; hostingresearch space31 mayhaveexpired acrosssessioninterval, inspectinventory first. API/web andDocker were stopped duringovernightinterval; no current project-owned listeners on3000/8000. Inspect beforestarting. Preserve oldQA/publicdata; futureTTL should target explicitly tagged public-demo workspaces, never blindly erase all prior local demos. Originalprototype checkout remains untouched.


## S12 local browser/platform verification — 21 November

Final39 real public-profile HTTP/PostgreSQL assertions passed, plus fresh domain/auth migration and populated-ledger downgrade guard. Both independent reviews clear through677ad32; narrow final refresh pending explicit Vercel API devCommand and evidence docs. Actual VercelCLI66.2.0 local Services router health/policy200, private-maintenance404, unauthenticated maintenance401. Explicit API devCommand fixed initial local startup. This is local evidence only, no cloud resources.

Ego-browser public entry/retrieve/fixture/edit/save/review/approve/source/Activity/Knowledge/Quality passed; offline Activity error recovered and five inbox widths had no overflow. Production build and audit0/0 passed after stopping localServices. DarkReader extension caused devhydration SVG warning and recolors light screenshot; do not claim clean lightvisual or native200%zoom/full keyboard-only proof. Report docs/verification/s12-public-demo.md. Ego space2 finished keep=[]; user space0 untouched.

Current public-profile local production web3002 and API8002 run from functional checkout; inspect/stop before builds. Verceldev stopped. No backgroundworker orpaidcall. Vercelteamselection still pending; no arbitraryteam orcostassumption. S12 remains unfinished/issue13open, Gmaildeferred/S13unfinished. GitHub partialPR/CI next.


## Current frontier — S12 hosting, 21 November

S12 local safeguard PR #25 merged facb4f94f8703f09a567f3baaea947e8ec2ee38a; final code-head99f6a59 CI44897430922 SUCCESS:280 genuine integration assertions+16 separately canned HTTP provider-contract assertions, migration/static/build/audit. Both final Spec/Standards refreshes through99f6a59 clear. Issue13 staysOPEN/blocked, not full S12 delivery. Continuation branch feat/s12-hosting from mergedmain.

Read-only Vercel account query: both my-team-7e4eb888 and alpa-pro-team are activeHobby plans. Account-view integration lists returnedempty. Costs endpoint returned404“Costs not found” for both; do not treat this aszero charges. Explicitteam choice remains pending; recommendationmy-team-7e4eb888. No project/database/integration/paidplan created ormodified. Current Marketplaceoffering/accountcost still requiresverification beforeprovisioning. No DeepSeek key deployed; publicfixtureonly. Clean lightvisual/fullkeyboard/postdeploy evidence remainpending, asdisclosed. S13blocked; Gmailrealverification explicitlydeferred.

Localproduction publicprofile web3002/API8002 remain running fromfunctionalcheckout, no backgroundworker. Inspectbeforebuild/restart. Ego space2 finishedkeep=[]; userspace0 untouched. Originalprototypecheckout retains its two preexisting screenshot modifications anduntrackedapps/web/AGENTS.md. No newpaidcalls orsecrets committed. PR/issuecomments preservefinalCI/review/accountfacts.
