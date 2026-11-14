# Proposed ticket breakdown — awaiting review

Retain the agreed S01–S13 vertical slices below. Each includes UI, API, persisted state, failure handling and verification after implementation. Split a slice further before implementation if it cannot fit a bounded delivery.

Verification uses the running API with a real disposable PostgreSQL database, browser journeys through ego-browser, and separately labeled fixture/live evaluations. No unit tests.

Only S01 becomes ready after setup and auth selection. Other slices remain blocked until genuine prerequisites are met. The parent specification is not an executable ready-for-agent ticket.



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
