# S03 knowledge verification

Local verification completed 17 November 2026; delivery resumed 18 November. Branch `feat/s03-knowledge`, based on delivered S02 `7023c1a`; implementation `7c208b0`, review fixes `3d8526a`.

- Private PostgreSQL storage for UTF-8 Markdown/text originals, source hash and version metadata. Admin upload queues a durable parse/index job; no static public source URLs.
- Worker leases, attempt count and token fencing persist. Interrupted leases recover after two minutes; three failed attempts stop retries. Sections and deterministic 64-dimensional fixture vectors commit atomically. This is a labeled fixture equivalent, not a provider embedding or quality result.
- Admin must inspect and explicitly publish a ready version. Agents/Viewers read published, unarchived sections only. Archive removes member visibility; worker/command lock order is document → version → job.
- `uv run python -m scenarios.s03`: **25 assertions passed**, actual HTTP/Better Auth/PostgreSQL/worker. Covers role/isolation, unsupported/oversized/invalid UTF-8/empty inputs, no partial publication, concurrent workers, persisted vectors, stale revisions, Viewer denial, archive exclusion, failure/retry bounds and expired-lease recovery. No mocks/unit tests.
- Ruff/Pyright, web lint/types/build and migration passed. CI now includes S01, S02 and S03 scenarios with real authentication rate-limit spacing.
- Ego-browser: local Admin command accepted an active synthetic workspace and rejected the expired prior demo; file upload, queued state without Publish, real worker processing, three inspected sections, explicit publication, archive via a second page, failed heading-only source and Retry indexing were verified.
- Repeated selection retains loaded sections. Archive in another page followed by Agent access and Refresh removes all stale sections/list entries. Reload hides upload controls for Agent. Mobile Back restores row focus.
- Both themes checked at 360, 390, 768, 1280 and 1440px without horizontal page overflow. Inspected screenshots: `s03-dark.png`, `s03-light.png`, `s03-mobile.png`.
- Independent Spec/Standards reviews identified redundant-selection and stale-refresh bugs; fixed in `3d8526a`, browser-verified and re-reviewed with no remaining actionable findings.

Limitations: first uploaded version per document; replacement is a new document. PDF support, provider embeddings, staff sign-in, retention cleanup and hosted demo are later slices. Native browser 200% zoom remains unverified. No live Gmail/AI or full accessibility certification claimed. No paid resources provisioned.
