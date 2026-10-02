# Easel Prompt Stack

Easel owns its agent loop and provider requests. It assembles the system prompt from repository-owned guidance and loads Skills only when requested.

## Prompt layers

1. `prompts/SOUL.md` — Easel voice and capability overview.
2. `prompts/AGENTS.md` — workflow and safety guidance.
3. The requested Skill `SKILL.md` and referenced resources, loaded through bounded runtime tools.
4. Optional profile content, scoped to the selected profile session.

Formerly these prompts were stored under `openclaw/workspace/`; they now live in `prompts/`. No workspace sync is needed.

## Profiles and memory

Profile text is included in the system prompt and persisted separately for each profile session. General sessions do not inherit a profile's content. Sessions and provider settings are stored under `~/.easel/`.

## Skills

Skills are discovered from `skills/openclaw/` (legacy directory name) and loaded on demand. Text outputs are created under `outputs/`; bounded file tools prevent traversal and refuse overwrites. External media and publishing scripts continue to use their documented provider settings and their own approval/safety checks.
