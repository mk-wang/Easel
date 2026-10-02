# Native Easel runtime

Easel runs its own provider-backed agent loop. OpenClaw is not installed, launched, or read by `setup`, `easel chat`, `easel skill`, or the Web chat endpoints.

## Model providers

Configure chat providers in the Web settings panel (stored in `~/.easel/providers.json`, mode `0600`) or set `OPENAI_API_KEY`/`OPENAI_BASE_URL`/`OPENAI_MODEL`, `ANTHROPIC_API_KEY`/`ANTHROPIC_BASE_URL`/`CLAUDE_MODEL`, or `EASEL_LLM_API_KEY`/`EASEL_LLM_BASE_URL` in the project `.env`. Environment values override `.env`; Web settings are authoritative when a selected provider has a saved key. Keys are never returned by settings APIs.

Both OpenAI-compatible Chat Completions and Anthropic Messages tool-use protocols are supported. Easel owns session history in `~/.easel/sessions/`; sessions are isolated by profile. The Web API retains token/activity/question/done/error SSE event types and per-turn replay logs.

## Tool boundary

The runtime can list/read bundled Skills and references, read and create text artifacts below `outputs/`, and run registered Python/Node/Bun scripts from a Skill `scripts/` directory. Interactive CLI and Web SSE chat display a session-bound approval card for each script, including its arguments and possible effects; rejecting, timing out, or stopping the turn prevents process launch. Background/non-interactive endpoints disable scripts because they cannot collect approval. Shell scripts, arbitrary commands, path traversal, and unregistered file paths are rejected. Script runtime is bounded by a timeout and output limit and receives a reduced environment. Existing artifacts are never overwritten by the output tool. Profile onboarding has a separate capability enabled only for that one enhancement turn: it may update existing six-dimension Markdown files in the selected profile, and reports success only when a file actually changed.

`ask_user` creates session-bound question cards; answers are validated and returned to the same tool loop. Pending cards are in memory and do not survive server restart or coordinate across multiple worker processes. External media generation and public publishing scripts may be invoked by the native runtime only after explicit per-run user approval; no live or paid action is performed during tests.

## Legacy skill namespace

`skills/openclaw/` is retained as a repository directory name to avoid mass path churn and preserve existing skill references. Its contents are Easel-owned Markdown instructions and scripts; it is not an OpenClaw runtime dependency. The agent core prompt files live in `prompts/`.

The Web server binds to loopback by default. Set `EASEL_HOST` explicitly to opt into another interface.
