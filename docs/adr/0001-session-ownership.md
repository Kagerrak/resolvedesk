# Better Auth owns sessions; FastAPI owns workspace authorization

Approved 14 November 2026. Use Better Auth with PostgreSQL-backed anonymous demo sessions, later adding staff sign-in for live workspaces. This avoids custom authentication cryptography and a paid identity account while preserving one maintained identity system.

Next.js exposes Better Auth and proxies application requests on the same origin. FastAPI validates each session through Better Auth's session endpoint and resolves memberships itself; it never trusts client-supplied user IDs or role headers. This adds one internal round trip per request but avoids coupling Python to Better Auth's cookie-signing implementation or accepting stale roles embedded in tokens. Session caching is disabled so revocation is observed immediately.

Workspace data lives in PostgreSQL with scoped lookups and composite ownership constraints. The public deployment remains blocked until S12 quotas, expiration cleanup and abuse verification are complete; local anonymous access is not yet a safe public service.
