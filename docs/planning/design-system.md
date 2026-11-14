# ResolveDesk brand and experience specification

Status: agreed visual direction; concrete values below are proposed implementation defaults. Validate them in rendered screens and accessibility checks. This document accompanies implementation-plan.md.

## Design context

Users are B2B software support agents and team admins working through a queue throughout the day. They need fast scanning, trustworthy source review, controlled replies, and visible exceptions. Viewers inspect work without changing it. Customers communicate through email and never enter this workspace.

Brand personality: **calm, precise, capable**. Emotional goal: confidence and concentration. Visual direction: contemporary editorial software, warm neutral surfaces, deep teal accents, distinctive readable typography, light and dark themes. Restrained density and clear hierarchy take priority over decorative effects. This context must be saved into the application's .impeccable.md before design skills run.

## Identity

- Product name: **ResolveDesk**. Wordmark uses this exact casing.
- Descriptor: **Support, grounded in knowledge.** Treat this as optional marketing copy, not repetitive navigation text.
- Primary logo: horizontal custom wordmark with a compact mark to the left. Use a carefully adjusted medium/semibold sans-serif wordmark; deliver paths for final exports plus an editable source. Keep generous counters and a slightly tighter wordmark rhythm than body copy.
- Logo mark: an original geometric conversation frame with an open lower corner and two aligned short source lines inside. Resolve the lower line into a restrained check-shaped terminal if it remains legible. It should suggest conversation plus verified knowledge without relying on a generic chatbot face, sparkle, brain, or borrowed product icon.
- First explore three simple vector constructions of this same idea. Compare at 16, 24, 32 and 48px before selecting one. Do not treat the concept as already visually validated.
- Asset deliverables: primary horizontal, stacked lockup, mark-only, light-background and dark-background versions, single-color black/white equivalents for reproduction, SVG sources, transparent PNG exports at 1x/2x, favicon SVG/ICO and app icons. Preserve legal font licensing. Include asset names and usage examples in the brand guide.
- Working minimum size: 120px horizontal wordmark, 16px mark; adjust if rendering shows poor legibility. Clear space at least half the mark's height. No stretch, glow, arbitrary recoloring or use of status colors as brand variants.
- Branding must work in navigation, login, demo landing, browser tab, README cover and social preview. No invented certifications, customer logos or performance claims.

## Typography

Proposed pair: **Manrope** for product headings/wordmark exploration, **Source Sans 3** for interface and reading. Use **IBM Plex Mono** only for identifiers or compact technical diagnostics. Verify licensing and self-host/subset WOFF2 assets during implementation; retain a usable fallback stack.

| Token | Size / line height | Use |
|---|---|---|
| type.caption | 12 / 16px | Secondary metadata, never essential long copy |
| type.label | 13 / 18px | Compact labels and table metadata |
| type.ui | 14 / 20px | Default controls, queue and navigation |
| type.body | 16 / 24px | Conversation and reply content |
| type.subtitle | 18 / 26px | Panel headings |
| type.h3 | 22 / 30px | Section heading |
| type.h2 | 28 / 36px | Page heading |
| type.h1 | 36 / 44px | Select onboarding/marketing headings |
| type.display | clamp(40px, 5vw, 64px) / 1.08 | Landing page only |

Weights: 400 body, 500 labels, 600 headings, 700 sparingly. Use tabular figures for counts/timing. Message width 60–75 characters; explain long citations without overflowing. Preserve browser zoom and text resizing.

## Color system

Hex values are seed values; store them as primitives and map semantic tokens. CSS may express equivalent OKLCH values after validating gamut and contrast. Surfaces are subtly warm; teal conveys selected state and primary actions, not every element. Meaning is always paired with text or icons.

| Semantic token | Light | Dark |
|---|---|---|
| canvas | #F6F5F1 | #131A18 |
| surface | #FCFCF9 | #1B2421 |
| surface.raised | #F0F0EA | #24302B |
| surface.hover | #E9ECE5 | #2A3831 |
| text.primary | #1C2B26 | #EDF2EC |
| text.secondary | #53635B | #BAC8BD |
| text.muted | #64736B | #9EAEA3 |
| border.subtle | #DCE2D8 | #34453B |
| border.control | #78897E | #7C9283 |
| action.primary | #146B63 | #86D3BE |
| action.primary.hover | #10574F | #A0E1CF |
| action.on-primary | #FCFCF9 | #14231C |
| selection.background | #DDEFE7 | #244A3B |
| focus.ring | #0B756C | #98DEC9 |
| status.success.text | #22623D | #A3D9AE |
| status.success.background | #E4F2E5 | #203E2D |
| status.warning.text | #80520C | #F0CB84 |
| status.warning.background | #FAEFD8 | #43371F |
| status.error.text | #A12C35 | #F3AFB4 |
| status.error.background | #FBE8E8 | #4B282D |
| status.info.text | #285C88 | #A9CDEB |
| status.info.background | #E6EFF7 | #243A4D |

Validate actual pairings for WCAG 2.2 AA: normal text 4.5:1, large text 3:1, essential controls/focus boundaries 3:1 where required. Subtle dividers are decorative and must not be the only cue identifying a control. Recheck disabled, selected, hover and error states independently. Do not claim seed values are fully audited until rendered checks pass.

## Tokens beyond color

- Spacing base: 4px. Scale: 0, 2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80.
- Radii: 4px compact controls, 8px inputs/buttons, 12px panels, 16px dialog; pill only for tags and compact statuses.
- Borders: 1px standard, 2px emphasis/focus. Focus: 2px ring + 2px offset, visible on every surrounding surface.
- Elevation: flat canvas and restrained panel separation; two shadow levels for floating menus/dialogs only. Specify matching dark-theme shadows.
- Control heights: 36px compact desktop, 40px standard, 44–48px touch. Do not reduce essential touch targets for visual density.
- Layout: rail 224px expanded/64px collapsed; queue 300–360px on wide screens; conversation flexible; evidence panel 320–400px when space permits.
- Breakpoints: 640, 960, 1280 and 1600px; adjust based on content failures, not device names. Use minmax/fluid widths and container queries where useful.
- Z-index layers: base 0, sticky 10, dropdown 20, overlay 30, dialog 40, toast 50. Tooltips must not trap focus or obscure their trigger.
- Motion: 100ms hover, 160ms control feedback, 220ms panel entrance; standard ease-out. Respect prefers-reduced-motion. No animation of reply submission that implies success before confirmation.
- Iconography: one coherent outline family, 16/20/24px, consistent optical weight; accessible text labels for icon-only actions. Logo is a separate original asset.
- Store primitive, semantic and component tokens separately; expose a documented token preview. No hard-coded palette values scattered across application components.

## Product information architecture

Primary navigation: **Inbox, Knowledge, Activity, Quality, Settings**. Workspace switcher at the top, connection health near the workspace rather than hidden in a developer menu. Show fixture/demo mode prominently but quietly.

### Core workspace

1. Queue: search, state/assignee filters, subject, customer, last activity and clear unread/exception state. Do not fill the page with metric cards.
2. Conversation: coherent customer/agent chronology, sender identity, attachments and timestamps.
3. Evidence: draft coverage, retrieved sources, source excerpts, freshness warning, missing knowledge and proposed ticket changes.
4. Composer: distinguish **Generate draft**, **Save draft**, **Approve and send**, and **Apply changes**. Consequential actions show exact targets and changed values. Viewers see read-only explanations.

At 1280px+ use rail + queue + conversation, with evidence shown alongside only if the conversation remains readable; otherwise make evidence a toggleable panel. At tablet widths show queue/detail routes with an evidence drawer. At mobile widths use a single panel with explicit Back navigation, Conversation/Evidence tabs and a reachable composer. All critical tasks remain possible without hover.

### Other journeys

- Onboarding: create isolated demo session or sign in, select workspace, inspect example ticket, open cited source, edit draft and complete a simulated approval.
- Knowledge: upload → parsing/indexing progress → inspect extracted sections → publish; show failed files and supported-format guidance.
- Connections: admin connects dedicated Gmail label, sees allowed scopes and last sync, tests connection and can disconnect.
- Activity: business-readable timeline, failed operations and safe recovery. Technical details are secondary disclosure.
- Quality: dataset/version selector, measured results, examples of failure and tradeoffs; explicitly distinguish fixture evaluation from real provider measurements.
- Public landing: short product explanation, one strong real screen, Try demo, architecture/README link; avoid a large marketing site before the product works.

## Component inventory

Document and render: wordmark/mark, navigation, workspace switcher, breadcrumbs, buttons, icon buttons, links, inputs, search, selects/comboboxes, checkbox, radio, switch, textarea/editor, form labels/help/errors, badges/status chips, avatar, queue row, table, pagination, tabs, document source excerpt, citation link, message bubble, draft composer, action review diff, alert/banner, toast, tooltip, popover/menu, drawer/dialog, loading skeleton, progress, empty state and error/retry state.

Each applicable component needs default, hover, focus-visible, active, selected, disabled, loading, error and success variants; light/dark and responsive behavior. Use accessible primitives; retain their keyboard behavior while giving them ResolveDesk's visual treatment. Include a /design-system route or equivalent gallery using real tokens.

## Tone and microcopy

Use specific, plain language. Avoid claims of certainty or numerical confidence derived only from a model's self-report.

- Empty inbox: “Your queue is clear.” Secondary action: “Load example tickets” in demo mode.
- No evidence: “I couldn't find a published source for this answer. Review the ticket or escalate it.”
- Stale draft: “The conversation or source material changed. Generate a new draft before sending.”
- Revoked connection: “Gmail needs reconnecting. Your saved drafts are safe.”
- Uncertain send: “Delivery is being checked. Don't resend yet.”
- Simulated action: “Demo reply recorded. No email was sent.”
- Budget exhausted: “AI generation is paused for this demo. You can still explore the inbox and sources.”

Errors explain what happened, what remains saved and the next useful action. Success messages reflect confirmed results only. Avoid blame, jargon and cheerful language around failures.

## Accessibility and verification

WCAG 2.2 AA target; semantic headings/landmarks, skip navigation, visible focus, keyboard-operable queue and composer, proper labels/error association, accessible dialogs and focus return. Announce streaming/progress without reading every token. Support 200% zoom, reduced motion, long names, empty fields, offline/slow network and keyboard-only use. Every chart has a text/table alternative.

Verify representative screens at 360, 390, 768, 1280 and 1440px in both themes, including long tickets, failed indexing, no evidence, stale approval, expired auth and read-only role. Use ego-browser for browser inspection and screenshot evidence. Build functionality before adding post-implementation browser checks; no TDD and no unit tests.
