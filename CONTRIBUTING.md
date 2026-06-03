# Contributing to tokenlab

This project uses [agent-forge](https://github.com/pthode/agent-forge) for AI-assisted development. All substantial changes flow through a pipeline of specialized agents — defined in `.claude/agents/` — orchestrated by Claude in `CLAUDE.md`.

## Common workflows

- **New feature:** run `/autopilot <description>` and answer the intake questions.
- **Bug fix or small change:** open Claude and describe the change — it routes to the right agent.
- **Upgrade the forge scaffold:** run `/forge-update`.

## Where things live

- Pipeline rules and routing table — `CLAUDE.md`
- Project invariants and non-negotiables — `CONSTITUTION.md`
- Agent definitions (live source of truth) — `.claude/agents/`
- Slash commands — `.claude/commands/`
- Upgrade history — `UPGRADING.md`

## Learn more

Full agent-forge documentation: <https://github.com/pthode/agent-forge>
