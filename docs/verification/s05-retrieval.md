# S05 retrieval verification

18 November 2026. Synthetic local data only. No unit tests, mocks, paid requests or AI quality claims.

## Implemented behavior

- Native PostgreSQL `vector(64)` storage; exact cosine ranking applies workspace, published status, model and archive filters before selecting at most five passages within fixture distance 0.65. No approximate or unmeasured hybrid ranking.
- Persisted Retrieval runs include ticket revision/query, fixture model, ranking method/version/parameters, selected source versions, ranked chunk references and distances. Composite foreign keys enforce workspace/version ownership.
- Ticket evidence UI distinguishes no run, empty evidence, retired sources, loading and recoverable failures. Citation requests reauthorize workspace membership and current source publication, and return exact version passages with PDF pages or text sections.
- Viewers inspect saved evidence but cannot create runs. Archived content is removed from historical excerpts/citation access without duplicating source text into retrieval history.
- Mobile Conversation/Evidence controls, keyboard citation focus/return, complementary themes.

## Executed verification

`uv run python -m scenarios.s05`: **30 real HTTP/PostgreSQL/pgvector/worker assertions passed**, after implementation. Includes deliberately similar private workspace-B source, unpublished/archive exclusions, empty runs, persisted reload, actual vector type and distance order, source-version/ranking provenance, PDF pages, invented/foreign citation denial, foreign ticket denial, Viewer rules, archive and membership revocation. Real invalid SQL inserts verify ownership constraints. Scenario-owned data is deleted afterward.

Python Ruff and Pyright, web ESLint and TypeScript, production build, and dependency audit passed. Next production process was stopped before each build and restarted after. Migration upgrades applied locally; fresh migration and S01–S05 regression are CI gates.

`npm view picomatch version` returned 4.0.7; the registry audit still reports that release affected by GHSA-fc5q-39xc-vjpf. Production audit passed. The existing narrowly approved development-only exception still expires 2 December 2026; no new exceptions.

## Ego-browser journey

Installed guide 2.2.1; used only ego-browser. Created a synthetic demo, observed explicit empty evidence, granted local-only Admin via approved command, uploaded the committed synthetic PDF through Knowledge, ran the actual worker, inspected and published through UI, then retrieved and opened a PDF citation. Passage matched version/page metadata. Opening focused H4; closing returned focus to the initiating citation button. Keyboard Enter opened the citation. Mobile Evidence hid Conversation, and Conversation restored it.

Widths 360, 390, 768, 1280 and 1440 in both themes showed no horizontal overflow and an accessible evidence panel. Screenshots visually inspected:

- [Desktop dark](images/s05-desktop-dark.png)
- [Desktop light](images/s05-desktop-light.png)
- [Mobile dark PDF citation and focus](images/s05-mobile-citation.png)

Real Better Auth rate limiting was encountered during repeated combined API/browser checks; UI showed “Sign-in is busy” and recovery guidance. Allowed reset without bypass. Final browser reload verification was rate-limited; saved-run reload is verified by separate real HTTP requests, not claimed as a successful final browser reload. Native 200% browser zoom remains unverified.

## Independent review

Separate Standards and Spec reviewers inspected `0bf32f2...608f68f`. Findings: persist ranking method/parameters; expose mobile Conversation/Evidence navigation. Both fixed in `428fa1c`; both reviewers rechecked the followup and reported no remaining actionable findings. The later scenario additions only extend genuine database/provenance checks.

No real-provider relevance/recall evaluation, hosted demo or Gmail verification is claimed. S06–S13 remain unfinished. Public deployment remains blocked by planned usage, cleanup, abuse and safe-delivery controls.
