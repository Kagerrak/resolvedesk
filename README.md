# ResolveDesk

Support, grounded in knowledge.

An AI-assisted B2B support product under construction. The local preview provides an isolated synthetic workspace, persisted ticket inbox, manual drafts, explicit ticket handling and audit history. S01–S06 are delivered, including limited live DeepSeek smoke verification. S07 approval is under verification; Gmail, broader quality evaluation and the hosted recruiter demo remain unfinished.

## Run the local fixture preview

Requires Docker, Node.js 22+ and [uv](https://docs.astral.sh/uv/). No AI or Gmail credentials needed.

```sh
python3 scripts/configure-local.py
docker compose up -d --wait
cd apps/api
uv sync --frozen
uv run alembic upgrade head
cd ../web
npm ci
npm run auth:migrate
npm run build
```

Start the API and web in separate terminals:

```sh
cd apps/api
uv run uvicorn resolvedesk.main:app --host 127.0.0.1 --port 8000
```

```sh
cd apps/web
npm run start
```

Open [localhost:3000](http://localhost:3000). Use this exact hostname for the session origin. Explore the sample inbox to create a Better Auth anonymous session and a unique persisted workspace. Search/filter the actual queue, save a manual draft, assign a ticket, change priority/status and inspect history. Saved drafts are not messages. Review and explicitly approve a saved reply to record simulated delivery; no email is sent. Conflicting edits require comparison before saving again. Reload preserves saved work and query filters. End demo session signs out. Sessions and workspace access expire after one hour.

The scripts generate local environment files without overwriting existing configuration. Never commit them. `.env.example` files show placeholders only. Docker data remains in a local volume when stopped; `docker compose down` stops the database without deleting it.

**Local preview only:** expiry denies access, but scheduled deletion/global abuse limits arrive in S12. Do not publicly expose this slice or store real data. No public hosted demo yet.

## Verify after implementation

With both processes running against a disposable local database:

```sh
cd apps/api
uv run python -m scenarios.s01
# Allow the real anonymous-session rate limit to reset between scenario suites.
sleep 61
uv run python -m scenarios.s02
uv run ruff check resolvedesk migrations scenarios
uv run pyright
cd ../web
npm run lint
npm run typecheck
npm run build
npm audit
```

The scenarios create actual Better Auth sessions and persists PostgreSQL records, then check isolation, concurrent creation, revocation, expiry, draft revisions, concurrent writes, explicit reopen, Viewer enforcement and audit persistence. They delete their own synthetic records afterward. No unit tests or mock database. Interactive browser QA uses ego-browser; unattended CI browser execution is not configured or claimed.

## Product and delivery

- [Implementation plan](docs/planning/implementation-plan.md) — canonical scope and acceptance criteria
- [Specification](https://github.com/Kagerrak/resolvedesk/issues/1) and [slice status](docs/planning/delivery-status.md)
- [Design system](docs/planning/design-system.md), [domain glossary](GLOSSARY.md), [architecture decisions](docs/adr)
- [Confirmed execution decisions](docs/planning/execution-decisions.md): infrastructure ≤ USD 25/month; AI allowance USD 20/month, separately enforced before live usage

Licensed under [MIT](LICENSE). Fonts retain their own SIL Open Font Licenses.

## Local knowledge authoring (S03)

Create a synthetic demo first. Open Knowledge from the inbox; its URL includes the workspace UUID. For local Admin verification only:

```sh
cd apps/api
uv run python -m resolvedesk.local_admin <workspace-uuid>
uv run python -m resolvedesk.knowledge_worker
```

Reload Knowledge after granting access. Upload a UTF-8 `.md` or `.txt` file under 256 KB, refresh until indexing is ready, inspect sections and explicitly publish the version. The worker uses deterministic 64-dimensional fixture hash vectors stored with chunks; these are not provider embeddings or measured AI quality. Original text stays in private PostgreSQL storage. Agents/Viewers can read only published, unarchived versions. Archive removes a source from published reads. A failed job can be retried up to three attempts; interrupted leases recover after two minutes.

The Admin command refuses non-local databases/origins, live workspaces and expired sessions. Public visitors remain Agents and cannot upload or publish. Use only synthetic English documents in this local preview. Staff sign-in, provider embeddings and public deployment remain later slices.

After implementation, run `uv run python -m scenarios.s03` against the local disposable database (space suites by 61 seconds for maintained authentication limits). The scenario runs the real parser/indexer directly; avoid running another worker simultaneously during that deterministic verification.

### PDF knowledge (S04)

Admins can upload synthetic text-based PDFs up to 2 MB and 20 pages through Knowledge. The existing worker extracts each page in a subprocess, persists page numbers and fixture vectors, and makes publication available only after successful indexing. Scanned/empty pages, encrypted files and malformed PDFs fail with recovery guidance; OCR is not provided. Download original source returns an authenticated attachment, with the same workspace/publication access rules as inspection.

Processing bounds: 15-second wall timeout, 10-second CPU limit, bounded decompression/parsing, 100,000 extracted characters and 500 sections. Linux also applies a 512 MiB address-space limit; macOS does not support that OS memory cap reliably. No rendering engines or external PDF executables run.

After migration, build and startup, run `cd apps/api && uv run python -m scenarios.s04`. Stop background workers during deterministic scenarios and leave 61 seconds between scenario suites to respect authentication limits. The committed PDF fixtures contain only synthetic verification content.

### Supporting evidence (S05)

From a ticket, use **Find supporting evidence**. ResolveDesk stores the ticket query/revision, fixture model, ranked source-version/chunk references and distances. Exact PostgreSQL pgvector cosine ranking considers only published, unarchived knowledge in that workspace; at most five passages within fixture distance 0.65 are returned. This threshold is a deterministic fixture rule, not confidence or measured relevance. No hybrid ranking or paid provider calls are enabled.

Saved evidence reloads with the ticket. Open a citation to inspect its authorized passage, version and PDF page or text section. Retired sources lose their excerpts and citation access; retrieve again after ticket/source changes. Viewers inspect existing runs but cannot create runs. Empty evidence explicitly recommends review or escalation.

After implementation, `cd apps/api && uv run python -m scenarios.s05` verifies real HTTP/PostgreSQL/pgvector behavior, including a similar private source in another workspace. Space scenario suites by 61 seconds for auth rate limits. Stop the production web process before any build and restart afterward.

### Draft generation (S06 delivered)

S06 was delivered in PR #21 with final CI 44472186034. Live DeepSeek compatibility and a six-example application-output smoke review are recorded in [S06 verification](docs/verification/s06-drafting.md); broader evaluation remains S11 work.

Run `uv run python -m resolvedesk.generation` from `apps/api` alongside the API and existing knowledge worker. Retrieve current evidence, then use **Generate demo draft**. An authorized published extract becomes a new saved draft revision; missing evidence produces an escalation draft. You can cancel queued/running work. Changes to the ticket, source or access discard stale generated results. Editing creates another saved revision and retains evidence references for human review. No generation sends email or changes ticket fields.

Public API generation is always fixture-only. For a local synthetic Admin workspace, the separately gated DeepSeek command is `uv run python -m resolvedesk.local_generation <workspace-uuid> <ticket-uuid>`. Configure DEEPSEEK_API_KEY only in ignored `apps/api/.env`; LIVE_AI_ENABLED defaults false. Keep it false until spending controls pass. Do not put credentials in chat, commands or Git. The command refuses remote endpoints, live workspaces, non-Admins, expired sessions and missing configuration.

Allowance accounting uses PostgreSQL serialization and conservative reservations: USD20 global/month, USD0.25/workspace session, USD0.10/request, 10 generations/session, one active run/ticket, 20KB encoded request and 2,048 output tokens. Actual token counts reconcile conservatively; uncertain provider acceptance/usage retains the full reservation and interrupted jobs are not automatically retried. Pricing expires 18 December 2026. These estimates are not provider invoices; external account usage is outside this ledger. Public real AI, cleanup and complete abuse controls remain S12 work.

After implementation: `uv run python -m scenarios.s06` verifies real HTTP/PostgreSQL/worker behavior and concurrent allowances; `uv run python -m scenarios.s06_provider` exercises the actual adapter against an explicitly canned local HTTP provider. The latter is contract verification, not live AI or quality measurement. Keep LIVE_AI_ENABLED=false for disposable allowance scenarios; respect 61-second spacing between auth scenario suites and browser journeys.

Escalation drafts use application-owned wording so they do not claim reviews or account actions already occurred. Provider citation IDs stay in internal evidence references, not customer reply text. General membership policy must not be used to diagnose an individual account. Every draft still requires human review.


### Human approval and simulated delivery (S07 under verification)

Save your draft, choose any proposed ticket changes, then select **Review demo reply**. Inspect the exact reply, source citations and changes before **Approve and record demo reply**. Uncited drafts require explicit acknowledgement. A changed draft, conversation, ticket or published source invalidates the review. Retrying the same approval checks its existing receipt instead of creating another message. Simulated delivery is restricted to synthetic demo workspaces and has no email transport. Separate **Apply ticket changes** commands also require explicit confirmation and persist authorization.

Run `uv run python -m scenarios.s07` from `apps/api` against the real running application/PostgreSQL after the implementation. It paces requests to respect the real sign-in limit. Allow one minute between suites and browser verification.
