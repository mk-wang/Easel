# Native Easel runtime

Easel runs its own provider-backed agent loop. OpenClaw is not installed, launched, or read by `setup`, `easel chat`, `easel skill`, or the Web chat endpoints.

## Model providers

Configure chat providers in the Web settings panel (stored in `~/.easel/providers.json`, mode `0600`) or set `OPENAI_API_KEY`/`OPENAI_BASE_URL`/`OPENAI_MODEL`, `ANTHROPIC_API_KEY`/`ANTHROPIC_BASE_URL`/`CLAUDE_MODEL`, or `EASEL_LLM_API_KEY`/`EASEL_LLM_BASE_URL` in the project `.env`. Environment values override `.env`; Web settings are authoritative when a selected provider has a saved key. Keys are never returned by settings APIs.

Both OpenAI-compatible Chat Completions and Anthropic Messages tool-use protocols are supported. Easel owns session history in `~/.easel/sessions/`; sessions are isolated by profile. The Web API retains token/activity/question/done/error SSE event types and per-turn replay logs.

## Tool boundary

The runtime can list/read bundled Skills and references, read and create text artifacts below `outputs/`, execute the novel-writer slopcheck through its dedicated bounded tool. The agent cannot invoke arbitrary skill scripts. Script execution is bounded by a timeout and output limit, receives a reduced environment, and blocks script names associated with publishing, authentication, upload, or paid generation. Output paths are resolved before access and existing artifacts are never overwritten by the agent tool.

`ask_user` creates session-bound question cards; answers are validated and returned to the same tool loop. Pending cards are in memory and do not survive server restart or coordinate across multiple worker processes. Media generation and public publishing are not executed by the native runtime yet; the existing standalone media and publishing scripts remain available as direct user-operated workflows.

## Legacy skill namespace

`skills/openclaw/` is retained as a repository directory name to avoid mass path churn and preserve existing skill references. Its contents are Easel-owned Markdown instructions and scripts; it is not an OpenClaw runtime dependency. The agent core prompt files live in `prompts/`.

The Web server binds to loopback by default. Set `EASEL_HOST` explicitly to opt into another interface.
