# ResolveDesk implementation plan

Status: agreed product brief and engineering execution plan, originally prepared 14 November 2026. Actual progress is recorded in delivery-status.md and session-handoff.md; planned requirements below are not completion claims.

**16 November amendment:** Command Bright (D) is the approved visual direction, superseding the initial warm editorial appearance. Better Auth is approved; infrastructure allowance is up to USD 25/month, separate from the USD 20/month AI allowance. Public repository exists; S01 PR #16 is open with passing CI; production adoption of D and S02–S13 remain outstanding.

Companions: design-system.md, GLOSSARY.md, skill-update-record.json. Job-market rationale: ../research/ai-automation-2026-11-14/recommendation.md.

## 1. Outcome and confirmed decisions

Build a polished B2B support workspace that retrieves approved knowledge, drafts source-grounded answers, proposes ticket changes, and leaves consequential decisions to a human. Demonstrate applied AI engineering through a working product with measured quality, real Gmail integration and safe failure handling.

Confirmed through the planning interview:

- Fictional B2B software support; staff-only product. Customers communicate by email, not through an AI portal.
- Owned ticket inbox plus one real connector: Gmail.
- Isolated workspaces with Admin, Agent and Viewer roles. All current published knowledge is shared with authorized members within its workspace. No per-document permission groups in v1.
- English-only curated Markdown, plain text and text-based PDF uploads; Admin-managed publication. No scanned-document OCR in v1.
- Every customer reply and consequential ticket action requires explicit human approval. No autonomous sending.
- OpenAI generation and embeddings, exact supported models/prices verified when implementing.
- Configurable USD 20/month ceiling for AI use by the public demo, plus strict per-session limits. Hosting, database and other infrastructure costs are separate.
- Public Kagerrak/resolvedesk repository and a recruiter-friendly hosted demo. Visitors use isolated synthetic data and cannot connect or access real Gmail.
- Calm editorial visual direction; warm neutrals, deep teal, distinctive typography and light/dark themes.
- No TDD, no red-green-refactor workflow, no unit tests. Implement first; verify externally observable behavior afterward through API/database integration checks, browser journeys, AI evaluations, static checks and manual review.

### Completion criteria

A reviewer can open the hosted demo, explore a ticket, retrieve cited knowledge, inspect and edit a draft, approve a simulated reply, and inspect the resulting audit trail. A workspace admin can separately connect a real dedicated Gmail label and complete the same flow with a real message. Published evaluation results distinguish deterministic fixture runs from actual provider runs. Fresh setup is reproducible from the README. No customer data, credentials or invented production metrics enter the public repository.

### Out of scope

Customer-facing chat, billing/subscriptions, account refunds or entitlement changes, voice AI, social channels, additional helpdesk connectors, scanned PDFs/OCR, multilingual support, custom model training, per-document audience groups, autonomous agents, complex microservices, Kubernetes and a complete helpdesk replacement.

## 2. Workflow and updated skills

The relevant Matt Pocock skills were refreshed from https://github.com/mattpocock/skills. See skill-update-record.json for the observed upstream commit and installed hashes. The updated suite uses **GLOSSARY.md**, **to-spec**, and **to-tickets**, superseding older CONTEXT/to-prd/to-issues conventions for this new project.

At execution time, check for updates again using the supported installation/update mechanism. Update only this suite, preserve local customization, avoid duplicate plugin/copy installations and do not claim success if verification fails. Read the refreshed SKILL.md files before invoking them. Do not install or invoke TDD to satisfy another skill's default.

Apply in order:

1. grill-me / grilling for unresolved product decisions. Do not repeat confirmed answers. Ask only genuine decision questions, with recommended answers; inspect the environment for factual answers. If remaining unknowns affect implementation, resolve them before dependent work.
2. setup-matt-pocock-skills once the new GitHub repository is reachable. Use GitHub Issues, single root glossary and docs/adr. Respect its setup confirmation steps; prepare concrete drafts first. Default triage vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix; confirm if the installed setup workflow asks.
3. domain-modeling to maintain the glossary and narrowly justified ADRs as decisions crystallize.
4. to-spec to publish the scoped product specification with implementation-first integration/browser/evaluation verification seams.
5. to-tickets to propose and then publish the approved vertical slices. Native blocking links where supported, otherwise explicit issue references. An issue whose blockers are unfinished must not be labeled ready-for-agent; use a blocked state/label and promote it when ready.
6. implement for one slice at a time. Its TDD defaults are explicitly overridden by the user. Do not use implement-spec merely to fan out the entire roadmap.
7. code-review and pr for bounded review and clear change evidence. Use skill-required review delegation when applicable. The spec/tickets and user constraints are the review baseline.

Use frontend-design and relevant design skills after recording confirmed Design Context in .impeccable.md. Use ego-browser for browser work. Keep build/review/deployment workflows legible and concise.

## 3. New repository bootstrap

Proposed application location: /Users/rommelclarino/projects/resolvedesk, separate from this planning workspace. Check for an existing directory/repository before creating it; never overwrite unrelated work. The build prompt authorizes initializing the new app and GitHub repo; this planning task itself does not create them.

Verify authenticated GitHub owner. Create public Kagerrak/resolvedesk only if the owner and name are available; reuse only when it is clearly this project, otherwise ask about the collision. Default branch main; working branches feat/s01-workspace, feat/s02-inbox, etc. Never use codex/ branch names. No destructive resets, force pushes or secret commits.

Before the first public push, inspect staged content for credentials, private data, real mailbox identifiers and provider responses. Commit only placeholder .env.example values. Configure README, ignore files, public license after an explicit license decision, agent instructions, CI, docs and GitHub issue templates. Record remote URL, issue links and actual verification results. Do not invent an external origin or repo URL if creation fails.

Preserve existing AGENTS.md/CLAUDE.md instructions; when neither exists, follow setup skill's choice step. Whichever is chosen must prominently state: no TDD, no unit tests, ego-browser for browser tasks, no codex/ branches. CI must not introduce unit-test scaffolding as an implicit convention.

### First execution questions, only if unresolved

The product interview is complete for planning. The implementing agent should inspect available tools and local auth before asking. Remaining genuine operational choices can include license, paid infrastructure provider/budget, deploy account access, and real Gmail OAuth app/verification constraints. Recommend Apache-2.0 or MIT with a brief explanation and obtain the user's license choice before publishing a license. Never request raw credentials in chat; use provider secret storage and documented setup. A blocked paid provisioning step must not stop fixture/local development or other independent work.

## 4. Domain model and behavior

Use the companion GLOSSARY.md as the seed. Add resolved concepts such as Retrieval run, Generation run, Published snapshot, Delivery attempt and Evaluation case when implementation requires them. Keep implementation details in architecture/spec documents, not the glossary.

### Core records

Workspace, User, Membership, Ticket, Message, Attachment metadata, Knowledge document, Document version, Indexed chunk, Published snapshot, Retrieval run, Generation run, Draft revision, Proposed action, Approval, Delivery attempt, Connector, Sync cursor, Audit event, Usage reservation, Evaluation dataset/case/run.

Every workspace-owned record has enforced ownership. Foreign-key/reference checks must reject references to another workspace, even if an identifier is valid. Role checks and workspace filtering apply in APIs, background jobs, retrieval, exports and source-download routes. Browser route hiding is not authorization.

### Role matrix

| Capability | Admin | Agent | Viewer |
|---|---|---|---|
| Read own workspace tickets and published knowledge | Yes | Yes | Yes |
| Edit ticket, draft, approve reply or permitted ticket action | Yes | Yes | No |
| Upload/publish/archive knowledge | Yes | No | No |
| Manage members or connect/disconnect Gmail | Yes | No | No |
| View content-bearing activity | Yes | Yes | Yes |
| View secrets or decrypted tokens | Never | Never | Never |
| Run paid evaluations/change budgets | Yes | No | No |

Demo visitors receive a limited Agent-equivalent session scoped to one disposable workspace, with connectors, invitations and paid admin actions unavailable. Demo roles/role-switching may be simulated only in a clearly labeled sandbox; it must never grant real permissions.

### Ticket and knowledge lifecycle

- Ticket: open → pending → resolved, with explicit permitted reopen to open. Assignment and priority are separate attributes. Sending does not silently resolve unless the user approves an explicit send-and-resolve action.
- Message: immutable conversation entry with sender identity and source identifiers; edits to a draft do not mutate received messages.
- Knowledge version: uploaded → processing → ready → published; failure and archive are explicit states. Only published, successfully indexed versions participate in retrieval.
- Document replacement does not overwrite citation history. Versioned source excerpts remain traceable, subject to permission/deletion policy.
- Drafts are editable revisions. Approval binds to the exact draft revision, conversation revision, proposed actions and relevant published-knowledge snapshot.
- New customer message, edited draft, changed action payload, source retirement/replacement or revoked permission makes previous approval stale. Recheck before dispatch; visibly request fresh review.
- Distinguish “saved”, “approved”, “queued”, “sending”, “sent”, “failed”, and “delivery uncertain”. An approval is not delivery confirmation.

### Human actions and grounding

Permit only internal ticket assignment, status, priority and tags in v1. No refund, billing or customer-account API tools. AI tools are narrow and read-only until an approved command is validated by the application.

The model receives untrusted ticket and document content as data. Never accept instructions inside a document to change policy, reveal unrelated context, call arbitrary URLs or execute tools. Only allowlisted document-upload parsing and scoped retrieval; arbitrary website crawling is out of scope.

Citations are application-validated identifiers for retrieved published chunks, never arbitrary source URLs invented by the model. A citation is not proof that a claim is supported: evaluate claim support and review examples. Missing, conflicting or stale evidence triggers a visible warning or escalation. Never present a model's self-reported numerical confidence as a calibrated probability.

## 5. Architecture and integration defaults

Use familiar foundations and add AI depth rather than infrastructure breadth:

- Web: Next.js + React + TypeScript, Tailwind token layer, accessible component primitives, TanStack Query where server state needs it. Choose stable compatible versions from official documentation at implementation time and pin lockfiles.
- API: Python/FastAPI + Pydantic, SQLAlchemy and Alembic.
- Data: PostgreSQL + pgvector, with workspace filters applied before retrieval results are exposed. Store queryable metadata and source-version relationships.
- Worker: one Python background-worker process with a durable PostgreSQL job table/leases initially. Add Redis only if a measured requirement justifies it; no second competing orchestration engine.
- Storage: S3-compatible private object storage; local compatible service in development. Signed downloads require authorization and short expiry.
- AI: provider adapter for OpenAI generation and embeddings. Verify supported structured-output/tool APIs, embedding dimensionality, model availability and pricing using official docs. Persist model, prompt, embedding and source-version metadata. Provider credentials are server-only.
- Auth: maintained authentication library/provider with server-validated sessions and explicit workspace memberships. Select a suitable maintained option after compatibility research; never write custom password cryptography. Protect state-changing requests, invitations and session expiration.
- Gmail: backend OAuth adapter with minimum practical scopes and a dedicated selected label. Verify current Google requirements, restricted-scope rules, available accounts and verification constraints before promising a broadly public connector. Start with manual/incremental polling; push notifications can follow later.
- Deployment: portable containers for API/worker and managed PostgreSQL with pgvector; web host compatible with Next.js; object storage. Select the actual provider after checking the user's accounts and separate infrastructure budget. Free hosting must not be promised without verification.

Module seams: Identity & Workspaces; Inbox; Knowledge; Retrieval; Reply Assistance; Approved Actions & Delivery; Gmail Connector; Usage & Evaluation. Keep providers behind narrow interfaces; avoid a generic agent framework until a concrete need exists. Do not install LangChain and LlamaIndex simultaneously for checkbox coverage. Direct provider APIs plus explicit retrieval are sufficient for v1; add one framework only when justified and documented.

### Gmail correctness

Validate OAuth state and redirect binding, encrypt refresh tokens at rest, support reconnect/revocation, use pagination and incremental cursors, deduplicate received messages by provider identity per connection, keep cursor advancement consistent with committed ingestion, and filter self-originated replies to avoid loops. Scope each job to its workspace and connector.

Approval and message-delivery creation must be transactional and reject duplicate submissions. Use durable delivery attempts with correlation identifiers and provider metadata. **Do not claim exactly-once external delivery.** Gmail may accept a send whose response is lost. Put ambiguous outcomes in “delivery uncertain”, attempt safe reconciliation against available provider identifiers, and require operator review before any resend that could duplicate an email. Retry only failures known to precede acceptance, with bounded backoff.

Disconnect stops future jobs and revokes/clears local credentials appropriately. Pending approved actions must recheck connection and approval validity. Real email requires an admin-connected workspace and explicit agent approval; public demo never sends email.

### Ingestion and deletion

Set supported MIME types, size/page limits and safe rendering. Text PDFs only; reject scans with useful guidance. Do not execute embedded content. Parse → inspect → publish; failed or incomplete indexing is not searchable. Reindex with versioned embedding metadata when the model/dimensions change.

Archiving removes a document from future retrieval; drafts depending on its current validity become stale. Deletion removes active source/chunk/object content with an auditable tombstone; historical records must not keep deleted text indefinitely under the guise of audit. Define and expose an explicit retention policy before live deployment. No indefinite storage of raw prompts, secrets, private content or visitor sessions.

### AI budget and public demo

Provide two explicitly labeled modes: deterministic fixtures with no provider credentials, and real-provider mode. A successful fixture run must not be described as a live AI result.

Enforce the USD 20/month public-demo AI allowance centrally, across visitor sessions and both embeddings/generation/evaluation jobs. Use atomic conservative spend reservations, per-request token caps, concurrency limits, per-session limits and measured usage reconciliation; release unused reservation after completion and fail closed on unknown budget state. Price configuration is versioned and verified; estimates are not provider billing guarantees. Add provider-side limits where supported and disclose possible accounting lag or price drift. Demo preparation and fixture evaluation should not consume live-provider budget unexpectedly.

Create an isolated short-lived synthetic workspace for each visitor session; clean it up on expiry. Enforce global/session storage and request quotas, rate limiting and abuse limits. Seed small published knowledge and representative tickets. Admin integrations and real-data upload are unavailable to visitors. Fixture mode remains usable when AI budget or provider access is unavailable.

## 6. Brand and UI/UX delivery

Implement the full companion design-system.md: original logo and mark assets, typography, semantic colors, both themes, spacing/radius/elevation/motion tokens, accessible components and documented states. Save design context before invoking design skills. Brand exploration is a bounded preparatory task; complete a real screen early rather than delaying product behavior for a large design exercise.

Screens: concise public landing/demo entry, sign-in/workspace selection, inbox queue, ticket conversation/reply/evidence workspace, knowledge upload/publish/detail, activity/recovery, quality/evaluation, Gmail connection/settings, member/role controls and a component/token gallery.

Design the desktop information layout and its tablet/mobile adaptation; never merely shrink the three-column layout. UI must clearly identify cited/uncited content, fixture/live state, stale drafts, read-only access, confirmed sends and uncertain delivery. Do not surface provider/framework jargon unless it helps the operator make a decision.

## 7. Verification policy

**Absolute constraints:** no TDD, no test-first coding, no red-green-refactor, no unit tests, no unit-test files or unit mocks that mirror implementation. These override skills and generated templates. Integration checks and browser/evaluation work are written after the corresponding behavior exists.

Allowed and required where relevant:

- Lint, formatting, TypeScript/Python static checks, builds and migration validation.
- API + real disposable database integration scenarios at public application seams, including authorization and transactions. Model/email calls may use explicit boundary fixtures for deterministic cases; do not replace the application/database with a mock graph.
- Browser journeys after implementation; use ego-browser for interactive exploration. Any automated browser runner must operate through the mandated browser workflow/capabilities rather than silently switching tools. If unattended CI browser execution is unavailable, state that clearly and retain manual browser evidence plus automated API/evaluation gates; do not claim CI coverage that did not run.
- AI evaluation harness covering retrieval and answer support, separately from deterministic integration verification.
- Manual responsive/accessibility review, keyboard journeys and clear screenshot evidence.

Per slice record commands/scenarios, pass/fail and limitations. Stop at meaningful evidence; do not add redundant checks. Fix material authorization, false-delivery or data-leak failures before closing a slice.

## 8. Clear vertical slices

Bootstrap/design decisions are bounded preparation. Every numbered slice below delivers a narrow complete user behavior across UI, API, persisted state and post-implementation verification. If a slice grows beyond one fresh context, split it into similarly complete user journeys before work starts. Dependencies are genuine gates, not an instruction to publish all unfinished work as ready.

### S01 — Enter an isolated workspace and inspect a sample ticket

**Blocked by:** repository/setup/confirmed auth choice. **Demo:** sign in or create an isolated demo session, select the permitted workspace and open a persisted ticket.

Deliver membership enforcement, one seeded ticket/message, working navigation, logo mark and first design tokens/themes. A second seeded workspace provides an isolation scenario. API reads and object lookup enforce ownership; Viewer cannot mutate. No purely visual fake workspace switcher.

**Accept:** reload preserves ticket; unauthorized workspace requests reveal no ticket content; expired sessions recover to sign-in. **Verify after implementation:** API/database role/isolation scenarios and browser sign-in/select/read journey in both themes.

### S02 — Handle a ticket through the owned inbox

**Blocked by:** S01. **Demo:** filter/search tickets, open a conversation, save a manual draft and change assignment/priority/status with explicit permission.

Persist domain states, audit changes and accessible queue/detail navigation. Viewer remains read-only. Mobile Back navigation and empty/error/loading states work. Avoid fixture-only filters.

**Accept:** updates survive reload; conflicting edits are surfaced; saved draft is not sent; ticket reopen is explicit. **Verify:** API/database state transitions and browser edit/filter/read-only journeys.

### S03 — Publish usable knowledge

**Blocked by:** S01. **Demo:** Admin uploads Markdown/text, inspects parsed sections, publishes a version and opens it from Knowledge.

Deliver private storage, durable parse/index jobs and source/version metadata; include embedding ingestion or its explicit fixture equivalent so published content is usable for S05. Agents/Viewers cannot publish. No partial publication.

**Accept:** rejected formats and oversized uploads explain recovery; failed jobs can be safely retried; archived sources stop appearing as published. **Verify:** API/upload/database/worker integration plus browser upload/publish/archive. Label fixture embeddings.

### S04 — Publish text-PDF knowledge with traceable pages

**Blocked by:** S03. **Demo:** upload a text-based PDF and inspect page-aware extracted passages before publication.

Extend the same lifecycle; preserve section/page locations for later citations. Reject a scanned PDF with an OCR-not-supported explanation; safe attachment rendering and object access.

**Accept:** extraction state/error visible; invalid or empty text never becomes published knowledge. **Verify:** integration against actual sample files and browser source preview, including long text and a scan rejection.

### S05 — Retrieve supporting evidence from a ticket

**Blocked by:** S02, S03. **Demo:** open a ticket, request relevant knowledge and inspect ranked excerpts with citations.

Implement workspace-scoped retrieval, configured embeddings/pgvector and optional lexical/hybrid ranking only if measured. Persist retrieval run with source versions; citation panel opens authorized source passage. Use S04 PDFs when ready, without blocking initial Markdown retrieval.

**Accept:** no unpublished/archived/cross-workspace sources; empty evidence is explicit; links cannot expose another workspace's objects. **Verify:** API/database/vector retrieval scenarios and browser citation navigation with a deliberately similar private source in workspace B.

### S06 — Generate and revise a grounded draft

**Blocked by:** S05. **Demo:** generate an answer, inspect sources, edit it and save a new revision; insufficient evidence creates an escalation draft instead.

Real provider adapter, structured response validation, application-validated citations and read-only tools. Preserve prompt/model/retrieval metadata without exposing secrets. Add first per-request usage reservation and caps before enabling paid requests; public real-AI access remains off until S12. Handle cancellation, schema failure and provider errors without losing saved work.

**Accept:** cannot reference non-retrieved citation IDs; no invented account-specific facts; low evidence is visible; fixture/live modes unmistakable. **Verify:** post-implementation API/provider-boundary integration, browser generation/edit/error and initial evaluated examples.

### S07 — Approve a precise reply and record simulated delivery

**Blocked by:** S06. **Demo:** review exact content and proposed internal ticket changes, approve, then see the simulated message and immutable activity history.

Bind approval to content/actions/conversation/source versions; invalidate on edits or changed evidence. Transactional delivery intent prevents duplicate UI submissions. Only approved commands may change assignment/status/priority/tags.

**Accept:** stale or Viewer approvals rejected server-side; duplicate submit records one intent; demo never emits real email. **Verify:** API/database stale/concurrent/double-submit scenarios and browser approve/edit/reapprove journey.

### S08 — Connect Gmail and import a real support conversation

**Blocked by:** S02; available OAuth setup. **Demo:** Admin connects a dedicated label, starts sync and reads an imported thread in the owned inbox.

Implement least-privilege OAuth, encrypted tokens, selected-label sync cursor, pagination, deduplication, reconnect and disconnect. Show last sync and errors. Visitors cannot connect accounts. Keep mapping between ticket/message and provider thread/message identities.

**Accept:** repeated sync creates no duplicates; connection scope respected; revoked auth stops safely; own outbound messages do not loop as new inbound tickets. **Verify:** deterministic API/connector-boundary integrations plus documented real dedicated-mailbox browser journey. If credentials unavailable, mark live verification blocked, not passed.

### S09 — Deliver an approved reply through Gmail safely

**Blocked by:** S07, S08. **Demo:** approve a response to an imported ticket, deliver to its verified thread/recipient and inspect confirmed status.

Revalidate recipient, role, workspace, source/conversation revision and connector immediately before dispatch. Implement durable delivery attempts, bounded safe retries, reconciliation and uncertain-delivery state. Prevent arbitrary model-selected recipients and headers.

**Accept:** edits/customer arrivals invalidate approval; duplicate click cannot produce a second intended send; unknown provider outcome cannot be blindly retried. **Verify:** API/database worker and connector-boundary scenarios for 429, revocation, lost send response and concurrent approval; one actual controlled email exchange.

### S10 — Diagnose and recover an operational failure

**Blocked by:** S03, S07; S08/S09 for Gmail recovery cases. **Demo:** open a failed indexing/sync/delivery operation, understand next action and recover without duplicating work.

Activity filters, correlation timeline, job leases/attempts, bounded retry, admin connector health and authorized operator recovery. Provide business-readable status with secondary technical detail. Include source archive/delete behavior and stale-draft impacts.

**Accept:** secrets/content outside member scope never appear in logs; uncertain delivery stays distinct from ordinary failure; job restart doesn't duplicate persisted effects. **Verify:** integration failure/restart scenarios and browser recovery walkthrough.

### S11 — Measure retrieval and answer quality

**Blocked by:** S06, S07. **Demo:** run an evaluation dataset, open aggregate results and inspect failed examples and source support.

Seed a fictional collaboration SaaS with 20–30 curated articles and 40–60 ticket cases; include billing-policy explanations, roles/permissions, troubleshooting, unknown requests, conflicting/stale sources and prompt-injection attempts. Separate tuning set from held-out cases. Include workspace-isolation probes; avoid real customer data.

Measure retrieval recall@k when expected source labels exist, citation validity, claim support through human-labeled examples or a disclosed calibrated rubric, abstention behavior, critical leakage/action violations, latency and cost. Define denominators. Model-based judging is supplementary and labeled; never call self-scoring ground truth.

**Accept:** run records dataset/prompt/model/source versions; fixture vs provider metrics distinct; report baseline and improved results honestly. Initial targets: zero observed cross-workspace disclosure or unapproved actions in the finite verification set; all emitted citation IDs valid; aim for recall@5 ≥ 0.85 on labeled answerable cases. Treat these as targets, not achieved claims or universal safety guarantees. Review answer-support rubric before setting a numeric quality release threshold.

**Verify:** post-implementation end-to-end harness against the running system and a manual review sample; CI runs cheap deterministic cases, live runs explicitly budgeted/admin-only. Quality UI renders persisted run results, not hard-coded charts.

### S12 — Let a recruiter explore a safe hosted demo

**Blocked by:** S07, S10, S11; deployment account/budget. **Demo:** a new visitor gets an isolated workspace, explores synthetic tickets, generates a bounded draft or uses fixtures, approves a simulated reply and sees the outcome.

Implement global atomic demo spend reservation, session quotas, abuse limits, TTL cleanup, no real connectors, fixture fallback, budgets and a minimal landing. Demo state isolation is server-enforced. CI/build/migration/deployment health and rollback/runbook cover the deployed configuration.

**Accept:** two visitors cannot see each other's work; exhausted budget preserves exploration; visitors cannot access real mailbox/admin routes; expiry cleans associated objects/content. Clearly distinguish the public demo from live connected workspaces. Prefer separate deployment/data boundary for the public demo.

**Verify:** integration concurrency/quota/expiry scenarios, post-deployment ego-browser journeys in both themes and keyboard/mobile layouts. Never provision paid resources above an agreed infrastructure budget.

### S13 — Finish the recruiter-ready product and handover

**Blocked by:** S04, S09, S12; all accepted core slices. **Demo:** follow the README from clean checkout, run local fixture mode, inspect live-mode setup, view branded product screens and the evaluation report.

Complete logo exports/brand guide, component gallery, responsive/accessibility/polish pass, architecture diagram, verified screenshots, known limitations, operator runbook and short walkthrough video/script. Document real Gmail OAuth requirements and live verification status. No fabricated testimonials, usage metrics or unmeasured time savings.

**Accept:** fresh setup works; public GitHub links resolve; all critical workflows have evidence; no unit tests/TDD artifacts were introduced; all material review findings resolved or explicitly disclosed. Do not call live Gmail complete if credentials/verification still block actual integration proof.

**Verify:** clean-environment smoke, lint/types/build, targeted integration/evaluation checks affected by final changes, manual visual/keyboard review and code-review against spec and repo standards. Avoid unnecessary broad retesting when nothing changed.

## 9. Delivery discipline and handoff

Each GitHub ticket records user-visible outcome, blockers, acceptance criteria, verification scenarios and out-of-scope boundaries. Keep the issue body behavior-oriented; concrete paths belong in repo planning docs. Link the source spec. Promote only the available frontier to ready-for-agent.

Each slice starts from a recorded base, lands on a feat/ branch with a concise commit/PR and evidence, and updates the plan's actual status. Avoid claiming completion from a UI screenshot when state/integrations are fixture-only. Stop for real blockers or decisions, not routine implementation choices. Required user actions should name the specific account/setup need and preserve independent progress.

The build agent's final handoff lists repository URL, demo URL, completed/open issue links, local startup steps, verified behavior, live/fixture distinctions, budget settings and unresolved external dependencies. Do not create the whole product in this planning workspace or silently publish the user's current directory.
