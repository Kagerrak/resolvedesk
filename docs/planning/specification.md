# ResolveDesk product specification

## Problem Statement
Support staff need grounded answers with traceable evidence and controlled delivery, without exposing customer information across businesses.

## Solution
An owned B2B ticket inbox with published knowledge, cited draft assistance, explicit human approvals and a Gmail connector. Customers use email only.

## User Stories
1. As a workspace member, I want isolated access so another business cannot read our support data.
2. As a Viewer, I want read-only access so I can inspect work safely.
3. As an Admin, I want to curate and retire knowledge so answers use approved evidence.
4. As an Agent, I want exact-content approval so edits or new messages cannot silently change what I authorize.
5. As an operator, I want uncertain sends distinguished from failures so recovery avoids duplicate email.
6. As a recruiter, I want an isolated synthetic session so I can explore without real customer access.
7. As a support product user, I want to sign in or create an isolated demo session, select the permitted workspace and open a persisted ticket.
8. As a support product user, I want to filter/search tickets, open a conversation, save a manual draft and change assignment/priority/status with explicit permission.
9. As an Admin, I want to upload Markdown/text, inspects parsed sections, publishes a version and opens it from Knowledge.
10. As a support product user, I want to upload a text-based PDF and inspect page-aware extracted passages before publication.
11. As a support product user, I want to open a ticket, request relevant knowledge and inspect ranked excerpts with citations.
12. As a support product user, I want to generate an answer, inspect sources, edit it and save a new revision; insufficient evidence creates an escalation draft instead.
13. As a support product user, I want to review exact content and proposed internal ticket changes, approve, then see the simulated message and immutable activity history.
14. As an Admin, I want to connect a dedicated label, starts sync and reads an imported thread in the owned inbox.
15. As a support product user, I want to approve a response to an imported ticket, deliver to its verified thread/recipient and inspect confirmed status.
16. As a support product user, I want to open a failed indexing/sync/delivery operation, understand next action and recover without duplicating work.
17. As a support product user, I want to run an evaluation dataset, open aggregate results and inspect failed examples and source support.
18. As a visitor, I want to receive an isolated workspace, explores synthetic tickets, generates a bounded draft or uses fixtures, approves a simulated reply and sees the outcome.
19. As a support product user, I want to follow the README from clean checkout, run local fixture mode, inspect live-mode setup, view branded product screens and the evaluation report.

The implementation plan is canonical for shared architecture and verification policy; update this specification and its GitHub issue whenever that policy changes.

## Implementation Decisions


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



## Testing Decisions


**Absolute constraints:** no TDD, no test-first coding, no red-green-refactor, no unit tests, no unit-test files or unit mocks that mirror implementation. These override skills and generated templates. Integration checks and browser/evaluation work are written after the corresponding behavior exists.

Allowed and required where relevant:

- Lint, formatting, TypeScript/Python static checks, builds and migration validation.
- API + real disposable database integration scenarios at public application seams, including authorization and transactions. Model/email calls may use explicit boundary fixtures for deterministic cases; do not replace the application/database with a mock graph.
- Browser journeys after implementation; use ego-browser for interactive exploration. Any automated browser runner must operate through the mandated browser workflow/capabilities rather than silently switching tools. If unattended CI browser execution is unavailable, state that clearly and retain manual browser evidence plus automated API/evaluation gates; do not claim CI coverage that did not run.
- AI evaluation harness covering retrieval and answer support, separately from deterministic integration verification.
- Manual responsive/accessibility review, keyboard journeys and clear screenshot evidence.

Per slice record commands/scenarios, pass/fail and limitations. Stop at meaningful evidence; do not add redundant checks. Fix material authorization, false-delivery or data-leak failures before closing a slice.



## Out of Scope


Customer-facing chat, billing/subscriptions, account refunds or entitlement changes, voice AI, social channels, additional helpdesk connectors, scanned PDFs/OCR, multilingual support, custom model training, per-document audience groups, autonomous agents, complex microservices, Kubernetes and a complete helpdesk replacement.



## Further Notes
All S01–S13 acceptance criteria in the agreed implementation plan apply. Targets remain unachieved until measured. Infrastructure requires a separately approved budget. Full specification: https://github.com/Kagerrak/resolvedesk/blob/main/docs/planning/implementation-plan.md
