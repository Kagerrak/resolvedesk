# Visual direction exploration

15 November 2026. The user rejected the first inbox's appearance and requested modern options before further feature work.

Run `cd apps/web && npm run prototype`, then open http://localhost:3100/inbox?variant=A.

- A — Studio: compact rail, ticket queue, central conversation and persistent evidence panel. Recommended for everyday support work.
- B — Editorial: horizontal navigation, paper-like conversation and source notes in a side margin.
- C — Command: dark operations workspace, compact ticket table above a conversation/evidence split.

Use the bottom switcher or left/right arrows. Search and select sample tickets, open the sample source, edit a simulated draft and record local review. All content is synthetic; no reply is sent, no provider is called and no state is persisted by prototype controls. Navigation labels beyond the inbox are visual only.

Prototype lives on feat/ui-direction-prototypes, outside main, on the existing /inbox route behind development-only variant selection. This explores layout and style, not a shipped product or complete accessibility audit. The prior production inbox and S01 work are retained. Initial exploration did not assume a winner; the accepted D direction is recorded below.

Verified with ego-browser: all three variants rendered and screenshots inspected; search reduces sample rows, sample draft can be edited and reviewed, source opens/closes, direction buttons work, no page overflow at 390px. ESLint and TypeScript checks pass. No automated tests added for this throwaway prototype. A page-level Dark Reader opt-out preserves the intended comparison palettes without altering browser extension settings.

## D — Command Bright refinement

The user's latest choice supersedes the earlier Editorial selection: keep C's Command layout and create a brighter prototype with stronger contrast. D preserves C for comparison at `/inbox?variant=C`; the new version is `/inbox?variant=D`.

Changes: brighter slate surfaces, near-white primary text, lighter secondary text, clearer borders, vivid lime actions, brighter customer avatars and larger supporting labels. This remains a simulated prototype, not the production redesign.

Verified 16 November 2026: ego-browser screenshot inspected at 1440px; no page overflow at 390px. Nine measured rendered text/background pairs all exceed 4.5:1 (lowest 6.95:1); see command-bright-contrast.json. This is a targeted contrast check, not a full accessibility audit. Lint and TypeScript checks pass.

## Accepted direction

16 November 2026: the user said “that is more like it” and requested a continuation prompt and record updates. **D — Command Bright** is the accepted direction for production refinement. This supersedes the earlier B selection. Preserve these prototypes as provenance; carry D into the functional product without its simulated behavior or development switcher.
