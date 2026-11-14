# Dependency research — 14 November 2026

- Next.js registry reports 16.4.6, React 19.3.1; Next's published peer range accepts React 19. Node 24.20.0 is available locally, above the documented minimum. https://nextjs.org/docs/app/getting-started/installation
- Better Auth registry reports 1.7.23. Candidate maintained session system with a PostgreSQL adapter and anonymous plugin; decision pending. https://better-auth.com/docs/installation and https://better-auth.com/docs/plugins/anonymous
- FastAPI, Pydantic, SQLAlchemy, Alembic and psycopg resolved together by uv; exact versions are recorded in uv.lock. https://fastapi.tiangolo.com/deployment/versions/
- PostgreSQL 17 with pgvector chosen for local compatibility; container digest will be pinned after pull. https://github.com/pgvector/pgvector
- Fontsource Manrope and Source Sans 3 assets are self-hosted packages; retain bundled OFL licenses. https://github.com/fontsource/fontsource

Package compatibility must also pass the application build and integration verification. Registry availability alone is not verification. OpenAI models/pricing will be verified before S06 paid requests are enabled.
