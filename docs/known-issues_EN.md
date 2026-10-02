# Known limitations

## Native agent

- The native agent reads Skills, references, and profiles, creates non-overwriting text artifacts, and can invoke registered Python/Node/Bun Skill scripts from interactive chat after a per-run approval card. Shell commands are never exposed. Background API calls cannot collect approval, so script tools are disabled there. Profile onboarding can edit only existing six-dimension Markdown files in the new selected profile; success is reported only after an actual file change. Account login remains in the workbench. Local Claude/Gemini/Codex CLI subscription login is not currently a native model provider; the previous no-API-key adapter depended on OpenClaw and is not reused by Easel. Use a configured API-compatible or Anthropic provider until a separately constrained CLI adapter is implemented.
- Provider requests currently return a complete model response per turn. SSE event replay is supported, but model token streaming is not yet incremental.
- `ask_user` cards are kept in Web process memory and do not synchronize across server restarts or multiple workers.
- Session serialization uses in-process locks; use a single Web worker, as in the default setup.

## Legacy OpenClaw notes

The installer, CLI, and chat APIs in this branch do not require OpenClaw. Historical gateway configuration and sync files remain in the repository for reference but are not part of the native runtime.
