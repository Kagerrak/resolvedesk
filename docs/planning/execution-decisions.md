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
