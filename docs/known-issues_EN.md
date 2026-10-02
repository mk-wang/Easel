# Known limitations

## Native agent

- The native agent currently handles text workflows: it reads Skills, references, and profiles, creates non-overwriting text artifacts, and runs the novel-writer slopcheck. It does not launch media generation, account login, or public publishing scripts. Those workflows remain available from the workbench or as user-operated scripts.
- Provider requests currently return a complete model response per turn. SSE event replay is supported, but model token streaming is not yet incremental.
- `ask_user` cards are kept in Web process memory and do not synchronize across server restarts or multiple workers.
- Session serialization uses in-process locks; use a single Web worker, as in the default setup.

## Legacy OpenClaw notes

The installer, CLI, and chat APIs in this branch do not require OpenClaw. Historical gateway configuration and sync files remain in the repository for reference but are not part of the native runtime.
