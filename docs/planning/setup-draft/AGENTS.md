# ResolveDesk agent instructions

- Never use TDD, test-first development, red-green-refactor, unit tests or unit-test scaffolding. Implement behavior first, then verify real API/database scenarios, browser journeys, AI evaluations and static checks.
- Use ego-browser for all browser work.
- Never create codex/ branches. Use main and descriptive feat/ or fix/ branches.
- Preserve unrelated work. Never commit secrets, customer data or real mailbox data.
- Keep answers concise; recommend the best course when useful.
- Read docs/planning/implementation-plan.md and docs/planning/design-system.md. Follow .impeccable.md for UI work.
- A slice is complete only after persisted behavior, API, UI, failure handling, verification, review and GitHub delivery.

## Agent skills

### Issue tracker

GitHub Issues in Kagerrak/resolvedesk. See docs/agents/issue-tracker.md.

### Triage labels

Use the five default triage labels; blocked slices must not be ready-for-agent. See docs/agents/triage-labels.md.

### Domain docs

Single-context: root GLOSSARY.md and docs/adr/. See docs/agents/domain.md.
