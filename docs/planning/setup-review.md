# Setup review

Status: approved by the user on 14 November 2026; installed as active configuration.

Confirmed: public Kagerrak/resolvedesk, main, GitHub Issues, root GLOSSARY.md, docs/adr, no TDD/unit tests, ego-browser and no codex/ branches.

Approved choices:

1. Create AGENTS.md using [the exact draft](setup-draft/AGENTS.md). No AGENTS.md or CLAUDE.md existed.
2. Keep default triage labels: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. Add blocked for incomplete dependencies.
3. Adopt [issue tracker](setup-draft/issue-tracker.md), [domain rules](setup-draft/domain.md), and [label mapping](setup-draft/triage-labels.md) as docs/agents files.
4. Approve [S01–S13 breakdown](ticket-breakdown.md), including dependencies and post-implementation verification already specified in the plan.
5. Recommended license: MIT, a short permissive license for recruiter inspection/reuse. Apache-2.0 is an alternative with explicit patent provisions. MIT approved.

Paid infrastructure and live Gmail remain external setup decisions. Independent fixture work does not require paid provisioning.
