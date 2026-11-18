# ResolveDesk

Support, grounded in knowledge.

An AI-assisted B2B support product under construction. The local preview provides an isolated synthetic workspace, persisted ticket inbox, manual drafts, explicit ticket handling and audit history. AI drafting, knowledge, Gmail and the hosted recruiter demo remain unfinished; no live-provider or quality results are claimed.

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

Open [localhost:3000](http://localhost:3000). Use this exact hostname for the session origin. Explore the sample inbox to create a Better Auth anonymous session and a unique persisted workspace. Search/filter the actual queue, save a manual draft, assign a ticket, change priority/status and inspect history. Saved drafts are not messages and cannot be sent yet. Conflicting edits require comparison before saving again. Reload preserves saved work and query filters. End demo session signs out. Sessions and workspace access expire after one hour.

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

The Admin command refuses non-local databases/origins, live workspaces and expired sessions. Public visitors remain Agents and cannot upload or publish. Use only synthetic English documents in this local preview. Staff sign-in, PDF parsing, provider embeddings and public deployment remain later slices.

After implementation, run `uv run python -m scenarios.s03` against the local disposable database (space suites by 61 seconds for maintained authentication limits). The scenario runs the real parser/indexer directly; avoid running another worker simultaneously during that deterministic verification.
