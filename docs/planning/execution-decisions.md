# Confirmed execution decisions

14 November 2026, interactive user answers:

- Better Auth with isolated anonymous demo sessions for S01; staff sign-in added for live workspaces.
- Infrastructure allowance: up to USD 25/month total for hosting, database and storage, separate from the USD 20/month AI allowance. Check current pricing and aggregate costs before provisioning. No paid resources provisioned yet.
- MIT, AGENTS.md, default triage labels, specification verification seams and S01–S13 breakdown previously approved.
- All unresolved questions must be interactive.

16 November 2026, design decision:

- Command Bright (D) is accepted as the direction for continued production development. The later C-with-brighter-colors request supersedes the earlier B/Editorial choice. Do not repeat the style interview.
- Preserve C and D prototypes as design provenance; rewrite D into the functional product, not simulated controls. Light-theme adaptation remains to be validated.
- Continue to forbid TDD, all unit tests and unit-test scaffolding. Implement first, verify public behavior afterward. Use ego-browser, descriptive feat/ or fix/ branches, and interactive questions only.

17 November 2026, local knowledge authoring:

- User approved a documented local Admin setup command for an existing synthetic demo session. It must reject live/remote workspaces; public visitors remain unable to upload. Staff sign-in is not pulled ahead of S03.
- S03 uses explicitly labeled deterministic fixture vectors, private PostgreSQL source storage and durable worker jobs; no provider spend or hosted resources.

18 November 2026, temporary dependency exception:

- User approved a narrow exception for GHSA-fc5q-39xc-vjpf (picomatch ReDoS) in development-only lint tooling. No patched release exists as of verification. Production audit has zero findings. CI continues auditing all dependencies and fails other moderate-or-higher advisories, audit failures, or this exception after 2 December 2026. No framework downgrade or blanket audit bypass. Remove the exception when a fixed dependency is available.

18 November 2026, provider update:

- User selected their DeepSeek API for generation for now, superseding the original OpenAI generation choice. Use a server-side DEEPSEEK_API_KEY, never credentials in chat or Git. Existing fixture embeddings remain explicit and unchanged.
- The USD20/month AI allowance and all request/session reservations, human approval, citation, isolation and public-demo restrictions still apply. No paid generation before spending controls pass; public API stays fixture-only until S12 controls are delivered.


19 November 2026, Gmail verification deferral:

- User chose to defer real Gmail verification for now. Do not ask for OAuth credentials or mailbox setup again during this deferred phase. No mailbox has been connected. Keep S08/S09 and S10 Gmail recovery verification unfinished; continue independently unblocked work. This is not evidence of live Gmail delivery.
