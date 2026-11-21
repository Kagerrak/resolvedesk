# S12 public-demo safeguards — local verification

21 November2026. Local behavior implemented on feat/s12-demo. Hosted deployment remains unfinished: user chose existing hosting, but the explicit Vercel team selection is pending. No resource, paid plan, public URL, real mailbox or public paid AI activation exists.

## Implemented behavior

Public-only ownership and provenance boundaries, independent approved source/version/chunk IDs, three synthetic conversations, parsed/indexed published fixture knowledge, ten-generation cap,30-search and100-write atomic quotas,20/hour public signup and workspace creation counters. Public signup reserves capacity before user persistence and stamps an input-protected origin marker. The profile rejects Admin authoring even after accidental membership elevation, nonpublic data access and paid-mode activation.

Fixture requests use the actual targeted generation worker and durable PostgreSQL queue. A queued interrupted fixture intent can be explicitly resumed without creating another job. Human approval remains exact, atomic, simulated and idempotent. No email transport or provider request runs in public mode. Saved intent IDs support recovery after a lost response.

Expiry revokes reads immediately. Bounded cleanup removes only tagged expired public workspaces and eligible marked anonymous identities (including capacity-denied/abandoned signups). It preserves unmarked local records, active orphan sessions, other memberships/workspace ownership and the global monthly allocation ledger. Maintenance requires a server-only credential; public startup refuses missing maintenance configuration or paid dispatch. Downgrades refuse nonempty public quota ledgers.

## Actual evidence so far

- 39 real HTTP/PostgreSQL/public-profile assertions passed through the final health and protected-marker checks. The test runs actual Next.js/FastAPI processes on3001/8001 and real Better Auth/PostgreSQL. It verifies source identity/isolation, exact citation access, synchronous durable fixture preparation/resume, human approval, generation/search/write concurrency at the last slot, exhausted-budget reading, accidental Admin/nonpublic membership denial, hourly creation/signup gates, actual expiry deletion, orphan identity cleanup/preservation, real Next maintenance forwarding and startup guards. The final harness also proves clients cannot unset the marker and that frontend health reaches the actual API and required domain/auth schema.
- The existing Better Auth guard was not disabled or weakened. Installed implementation requires a quiet minute after its request threshold; the harness pauses every40 responses. Earlier verification used an incorrect draft method (corrected to the real POST endpoint), then hit this maintained busy guard before proper spacing. These were not accepted as successful runs.
- Ruff/Pyright, web types/lint/production build pass. Fresh empty database domain migration roundtrip and Better Auth migration passed, including the new protected user column. Existing local database/ledger preserved at43,494 microUSD; temporary migration database removed. A separate real PostgreSQL migration check rejected downgrade with a populated signup ledger and preserved the counter, then completed the empty-ledger downgrade/upgrade. Its temporary database was removed.
- Independent fresh-context Spec/Standards reviews found one shared P2: signup identities rejected before workspace creation could escape cleanup. Fixed by the pre-insert public identity reservation and protected origin marker; both reviewers cleared677ad32. Final hosted/CI evidence remains pending.
- Root compose project name is fixed to resolvedesk. An accidentally created empty worktree-named container was stopped and removed before use; the original resolvedesk PostgreSQL volume and allocation ledger were restored/preserved. No old QA data was erased.

## Deployment evidence pending

The proposed configuration is based on current official Services/FastAPI/binding documentation, with only the web service publicly routed. No platform deployment or private-route assertion has been fabricated. Actual selected account/Marketplace plan, aggregate cost, database provisioning/migration, cloud health/private routing, scheduled cleanup and post-deployment two-visitor browser evidence remain gates. S08/S09 and full S10 Gmail recovery stay explicitly deferred; S13 remains unfinished.

## Browser and platform-local evidence — 21 November

Pinned Vercel CLI66.2.0 loaded the actual Services configuration and ran both services locally. Its first API startup needed an explicit uvicorn dev command; that is now configured. Through the real local service router, /api/health and public-policy returned200, unauthenticated maintenance returned401 and the private internal-maintenance path returned404. This establishes local binding/routing behavior, not a cloud deployment or a JSON-schema validation claim.

Ego-browser verified a fresh public visitor receiving three conversations and four published sources, retrieval, real durable fixture generation, editing/saving, exact-reply review, explicit simulated approval, recorded conversation/history, retained source navigation and read-only Knowledge/Quality. Activity showed the actual completed generation and recorded reply. An offline refresh exposed a connection error; reconnect/refresh restored the recorded operation. Public Quality had no copied private evaluation runs and linked the disclosed report. No upload input was available in the visitor flow.

Inbox document widths equaled scroll widths at360,390,768,1280,1440 CSS pixels. The production build was made only after stopping the local Vercel development stack, then served on3002 with its actual API on8002. Reload retained the approved reply and source provenance. Screenshots below were inspected. Dark Reader is active in this browser profile: it injected the SVG attributes behind the development hydration warning and also recolored the light-theme screenshot. The application toggled data-theme correctly, but these screenshots do not establish an uncontaminated light-theme visual check. Native200% browser zoom and full keyboard-only public journey remain unverified.

- [Production inbox, light setting with extension recoloring](images/s12-public-light.png)
- [Production inbox, dark setting](images/s12-public-dark.png)
- [Production mobile inbox](images/s12-public-mobile.png)

Final production build passed; dependency audit returned0 production and0 development findings on21November. Registry latest picomatch remains4.0.7; the previously approved narrow exception remains unchanged and expires2December. No S12 paid provider call or infrastructure provisioning occurred.


## GitHub delivery of local safeguards

PR [#25](https://github.com/Kagerrak/resolvedesk/pull/25) merged as facb4f94f8703f09a567f3baaea947e8ec2ee38a. Final code-head99f6a59 [CI44897430922](https://github.com/Kagerrak/resolvedesk/actions/runs/44897430922) passed280 genuine integration assertions (39S12) and16 separately canned local HTTP provider-contract assertions, domain/auth migrations, static checks, production build and audit. Final narrow Spec/Standards refreshes through99f6a59 both returned no actionable findings. This is local safeguard delivery only; issue13 remains open for the outstanding deployment and browser gates above.
