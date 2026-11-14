# Dependency research — 14 November 2026

- Next.js registry reports 16.4.6, React 19.3.1; Next's published peer range accepts React 19. Node 24.20.0 is available locally, above the documented minimum. https://nextjs.org/docs/app/getting-started/installation
- Better Auth registry reports 1.7.23. Candidate maintained session system with a PostgreSQL adapter and anonymous plugin; decision pending. https://better-auth.com/docs/installation and https://better-auth.com/docs/plugins/anonymous
- FastAPI, Pydantic, SQLAlchemy, Alembic and psycopg resolved together locally by uv; manifests and the lockfile will be delivered with S01, not this setup commit. https://fastapi.tiangolo.com/deployment/versions/
- PostgreSQL 17 with pgvector chosen for local compatibility; container digest will be pinned after pull. https://github.com/pgvector/pgvector
- Fontsource Manrope and Source Sans 3 assets are self-hosted packages; retain bundled OFL licenses. https://github.com/fontsource/fontsource

Package compatibility must also pass the application build and integration verification. Registry availability alone is not verification. OpenAI models/pricing will be verified before S06 paid requests are enabled.

## S01 verified resolution

Web dependencies are now delivered in apps/web/package-lock.json and API dependencies in apps/api/uv.lock. Better Auth 1.7.23 is approved and session migration/real HTTP scenarios pass. The TypeScript-ESLint minimatch dependency is overridden to patched 11.0.1; lint and build validate its use. ESLint 10 uses the maintained Next, TypeScript and React Hooks plugins directly because the aggregate Next config still includes plugins whose declared peers stop at ESLint 9. No peer override flag is required. The resulting npm audit has zero reported vulnerabilities (14 November 2026); this is a point-in-time registry check, not a security guarantee.
