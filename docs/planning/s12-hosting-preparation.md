# S12 hosted demo preparation

21 November2026. Local public-demo behavior is in progress on feat/s12-demo. S11 delivered PR24 / merge822d81d; real Gmail remains explicitly deferred. No hosted resource, database, paid plan or public URL has been provisioned.

User chose the existing hosting account. Vercel is authenticated asKagerrak. Explicit team selection remains pending: my-team-7e4eb888 (recommended) or alpa-pro-team. Do not infer the selected team or reuse another application's database.

## Proposed deployment

One dedicated Vercel project with two services: Next.js is the only public entry; FastAPI is private and reached through the API_URL service binding. API session validation calls the web service through AUTH_URL. Application authorization still validates the actual Better Auth session and public workspace ownership; a platform binding is not authorization.

A separate Neon PostgreSQL database stores only public synthetic demo data. Local evaluation/QA data and any future live mailbox data remain outside that database. No DeepSeek key is deployed, LIVE_AI_ENABLED=false, PUBLIC_DEMO_ONLY=true. The public profile refuses paid dispatch and Admin authoring, even if a membership is accidentally elevated. A server-only maintenance credential is required before public startup.

Public fixture preparation uses the same durable PostgreSQL generation queue and targeted worker inside the request. No continuously running worker is required. An interrupted queued fixture can be explicitly resumed without a second generation intent; expired running attempts fail safely. Existing CLI workers remain available for local/operator use.

Existing and new session safeguards: ten generations,30 searches,100 saved actions,20 new public sessions/hour and50 active public sessions. Counters are atomic; exhausted quotas retain read access. Each visitor receives independent source/version/chunk IDs and three authored conversations. Repository-approved source content is parsed/indexed synchronously during initial seeding; no visitor upload or invented human publication is involved.

Only explicitly tagged expired public workspaces are cleaned, with associated content and eligible anonymous users. Previous untagged local demos and the monthly allocation ledger are preserved. Cleanup runs on new public entry and scheduled daily at03:00UTC. Access ends after one hour; operator health checks must monitor scheduled cleanup failures rather than promise deletion during an outage.

## Current pricing evidence — verify the actual selected account/Marketplace plan before provisioning

- [Vercel Services](https://vercel.com/docs/services): beta on all plans; [bindings](https://vercel.com/docs/services/bindings) provide deployment-aware private URLs. [Configuration reference](https://vercel.com/docs/services/config-reference) supports the checked-in service configuration.
- [Vercel pricing](https://vercel.com/docs/pricing): Hobby has included function/traffic allowances; this is not an unlimited-capacity claim. Account plan and current shared usage still need checking.
- [Daemon limits](https://vercel.com/docs/daemons/limits): Hobby includes420GB-hours/month; even one1GiB continuous worker would exhaust it before a full month. The proposed public profile therefore runs on demand.
- [Neon pricing](https://neon.com/pricing): direct Free plan currently lists100CU-hours,1GB storage and5GB transfer per project, with compute suspension at the monthly compute/transfer limits. It is not an always-on uptime guarantee. Marketplace offerings can differ; select and inspect an explicitly zero-cost plan before creating a dedicated database. Do not upgrade or enable metered add-ons by implication.

Target incremental recurring cost:USD0 using verified free plans and pausing at their limits. The existing approved maximum remainsUSD25/month total infrastructure, separate fromUSD20/month AI allowance. A plan requiring more must be redesigned or brought back with a concrete cost proposal. Existing paid account charges must be disclosed if applicable; current total is not yet verified because the team is unresolved.

## Release sequence

1. Complete real API/PostgreSQL concurrency, expiry/cleanup, no-connector and fixture-recovery scenarios, ego-browser journeys, independent review and CI.
2. Resolve the existing Vercel team, inspect its plan/usage and installed database integrations, then prepare a concrete resource plan within the cap. No unrelated project or store is modified.
3. Use an isolated deployment checkout/directory for Marketplace credential pulls. Do not overwrite apps/web/.env.local or apps/api/.env. Both Git and deployment ignore rules exclude environment files, caches and local environments. Generate the real maintenance/auth secrets locally and store them only in ignored files/provider settings; never print or commit them.
4. Configure a dedicated production database; preserve a separate preview database boundary. Do not inject production credentials into unverified previews. No migration runs as an automatic build command.
5. Apply domain and Better Auth migrations once against the dedicated database, deploy the reviewed commit, check real health/policy and private API routing, and perform two-visitor browser verification before advertising the URL.
6. Check scheduled maintenance with its real credential without exposing it, inspect actual database expiry cleanup and verify provider usage/cost configuration. Record actual URLs, plans, migration/deployment IDs and evidence.
7. Roll back only to a previously verified S12 release with the public guards. For an initial failed release, keep public access disabled until a verified S12 build exists. Never downgrade/drop a nonempty public/evaluation ledger to make a rollback pass.

VercelCLI global28.11.0 remains untouched; an ephemeral pinned66.2.0 invocation supports current Services/FastAPI features. Skill checks21November found applicable code-review/pr/domain-modeling files unchanged at upstreamabeeaf95660ba9e8b7c753eb38f441ca707a8823; local customizations preserved. Ego-browser guide2.2.1 verified. TDD excluded.
