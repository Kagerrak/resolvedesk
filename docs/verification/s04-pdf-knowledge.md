# S04 text-PDF knowledge verification

18 November 2026. Implementation 630a4cf, branch feat/s04-pdf-knowledge; based on S03. Delivered in PR #19, merged as fec794bd on 18 November 2026; issue #5 closed.

- Real private PDF upload, PostgreSQL binary originals, durable existing job lifecycle, isolated pypdf extraction, page-aware chunks and explicit Admin publication. Original downloads enforce the same workspace/publication access and return attachment, nosniff, sandbox and no-store headers.
- Limits: 2 MB, 20 pages, 100,000 extracted characters, 500 sections, 15-second wall timeout, 10-second CPU cap and parser/decompression work bounds. Linux additionally caps address space at 512 MiB. macOS cannot reliably apply that OS memory limit; its other bounds remain active. A first macOS run exposed this portability issue; corrected before successful scenarios.
- `uv run python -m scenarios.s04`: **22 assertions passed** against actual HTTP/Better Auth/PostgreSQL and the actual parser subprocess. Synthetic committed PDFs cover two pages with long text split into four bounded passages, page identity, persistence, role/workspace access, original byte identity, publication/archive, size/signature rejection, and scanned/encrypted/malformed/21-page failures with no partial publication. No unit tests or mocks.
- `uv run python -m scenarios.s03`: **25 assertions passed** after spacing for the real authentication rate limit. An earlier overlapping run hit that rate limit; retry after cooldown passed without weakening it.
- Ruff, Pyright, web ESLint/TypeScript and production build passed. Schema migrated to s04_pdf_sources. CI includes S04 after the existing suites with 61-second spacing.
- Ego-browser: Admin upload → queued → actual worker → four sections labeled Page 1, Page 1, Page 2, Page 2. Original browser download matched original bytes; explicit publication succeeded. Scanned PDF showed OCR-not-supported recovery, no Publish control and zero sections. Refresh clears an obsolete queued notice.
- No horizontal overflow at 360, 390, 768, 1280 and 1440px in both themes. Mobile keyboard Tab from original download reached Publish with visible focus. Inspected screenshots: s04-pdf-dark.png, s04-pdf-light.png, s04-pdf-mobile.png, s04-scanned-failure.png. Rendered fixture inspected for legible complete pages.
- Independent Standards review: no actionable findings, including approved advisory-specific audit script. Independent Spec review: no code defects; requested long-text/browser evidence was added and verified as above.

Sources consulted: [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html), [security](https://pypdf.readthedocs.io/en/stable/user/security.html), [configuration](https://pypdf.readthedocs.io/en/stable/modules/configuration.html). pypdf 7.1.0 is locked.

Limitations: no OCR, rendered in-app PDF viewer, provider embeddings or new document-version authoring. Sources remain inert extracted text plus authenticated original attachment. Native 200% browser zoom and full accessibility certification are not claimed. S05–S13, hosted demo and real Gmail/AI verification remain unfinished.

CI delivery evidence: https://github.com/Kagerrak/resolvedesk/actions/runs/44243139958 passed on Linux: 23 S01 + 29 S02 + 25 S03 + 22 S04 assertions, migrations, static checks, production build and the approved scoped security check.
