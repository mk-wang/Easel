"""OpenClaw-independent Easel text agent runtime with bounded tools."""
from __future__ import annotations
import json, os, re, subprocess, sys
from pathlib import Path
from typing import Any, Callable, Iterator
import httpx

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills" / "openclaw"
OUTPUTS = ROOT / "outputs"
STATE = Path(os.environ.get("EASEL_STATE_DIR", Path.home() / ".easel"))
MAX_RESULT = 32000

class RuntimeErrorBase(RuntimeError):
    pass

def _safe_under(root: Path, relative: str) -> Path:
    base = root.resolve()
    target = (root / relative).resolve()
    if target != base and base not in target.parents:
        raise ValueError("path is outside the allowed directory")
    return target

def _usable_credential(value: str) -> bool:
    normalized = (value or "").strip().lower()
    return bool(normalized) and not any(marker in normalized for marker in ("replace_me", "your-api-key", "your_api_key", "your-key", "your_key"))


def provider_config():
    # Read project .env for setup/CLI use without logging its contents. Process env wins.
    file_env: dict[str, str] = {}
    env_path = ROOT / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                if name.isidentifier(): file_env[name] = value.strip()
    except OSError:
        pass
    def get(name: str, default: str = "") -> str:
        return os.getenv(name, file_env.get(name, default))
    # Web model settings are stored by Easel itself; no OpenClaw config is consulted.
    try:
        from easel.native_settings import load_config
        cfg = load_config()
        providers = cfg.get("providers", {})
        selected = providers.get(cfg.get("primary", ""))
        if isinstance(selected, dict):
            credential = str(selected.get("key") or get(str(selected.get("credentialEnv") or "")))
            if not selected.get("baseUrl") or not _usable_credential(credential):
                raise RuntimeErrorBase("所选 Easel 模型供应商缺少 Base URL 或 API Key")
            return (str(selected["baseUrl"]).rstrip("/"), credential,
                    str(selected.get("model") or "gpt-4o"), str(selected.get("protocol") or "openai"))
    except (ImportError, OSError, ValueError):
        pass
    if get("EASEL_LLM_BASE_URL"):
        key = get("EASEL_LLM_API_KEY").strip()
        if not _usable_credential(key): raise RuntimeErrorBase("请设置有效的 EASEL_LLM_API_KEY")
        return get("EASEL_LLM_BASE_URL").rstrip("/"), key, get("CLAUDE_MODEL", "deepseek-chat"), "openai"
    if _usable_credential(get("OPENAI_API_KEY")):
        return get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"), get("OPENAI_API_KEY").strip(), get("OPENAI_MODEL", "gpt-4o"), "openai"
    if _usable_credential(get("ANTHROPIC_API_KEY")):
        model = get("CLAUDE_MODEL", "claude-sonnet-4-6").split("/", 1)[-1]
        return get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").rstrip("/"), get("ANTHROPIC_API_KEY").strip(), model, "anthropic"
    raise RuntimeErrorBase("未配置模型凭据：设置 EASEL_LLM_API_KEY、OPENAI_API_KEY 或 ANTHROPIC_API_KEY")

def tool_schemas(*, profile_edit: bool = False, script_execution: bool = True):
    specs = [
        ("list_skills", "List Easel skills", {}, []),
        ("read_skill", "Read skill guide/reference", {"skill":{"type":"string"},"file":{"type":"string"}}, ["skill"]),
        ("read_output", "Read a text file under outputs/", {"path":{"type":"string"}}, ["path"]),
        ("write_output", "Create a text artifact under outputs/ without overwriting", {"path":{"type":"string"},"content":{"type":"string"}}, ["path","content"]),
        ("run_novel_check", "Run novel-writer deterministic slopcheck on an output", {"path":{"type":"string"}}, ["path"]),
        ("ask_user", "Ask the user a structured question and wait for their selection", {"questions":{"type":"array","items":{"type":"object"}}}, ["questions"]),
    ]
    if script_execution:
        specs.append(("run_skill_script", "Run a registered Python/Node/Bun script from a skill after showing an approval card", {"skill":{"type":"string"},"script":{"type":"string"},"args":{"type":"array","items":{"type":"string"}}}, ["skill","script"]))
    if profile_edit:
        specs.append(("update_profile_file", "Update one existing Markdown file in the selected profile during profile enhancement only", {"file":{"type":"string"},"content":{"type":"string"}}, ["file","content"]))
    return [{"type":"function","function":{"name":n,"description":d,"parameters":{"type":"object","properties":p,"required":r,"additionalProperties":False}}} for n,d,p,r in specs]


def _execute_registered_skill_script(skill: str, script: str, argv: Any) -> str:
    """Execute only a concrete script below one registered skill after caller approval."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", skill): raise ValueError("invalid skill name")
    if not isinstance(argv, list) or len(argv) > 64 or any(not isinstance(a, str) or len(a) > 2000 for a in argv):
        raise ValueError("script arguments must be at most 64 strings of 2000 characters")
    scripts_dir = _safe_under(SKILLS, skill) / "scripts"
    target = _safe_under(scripts_dir, script)
    if target.parent != scripts_dir.resolve() or not target.is_file(): raise ValueError("script is not registered under this skill")
    if target.suffix == ".py": command = [sys.executable, str(target), *argv]
    elif target.suffix in {".js", ".mjs", ".cjs"}: command = ["node", str(target), *argv]
    elif target.suffix == ".ts": command = ["bun", str(target), *argv]
    else: raise ValueError("only registered Python, JavaScript and TypeScript scripts can run; shell scripts are disabled")
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "TMPDIR", "TEMP", "SYSTEMROOT", "LANG", "LC_ALL", "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY", "no_proxy"} or k.startswith(("EASEL_", "OPENAI_", "ANTHROPIC_", "GEMINI_", "WECHAT_", "WECHATSYNC_", "XHS_", "BILIBILI_", "DOUYIN_", "VIDEO_", "VOICE_", "SILICONFLOW_", "MINERU_"))}
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["EASEL_ROOT"] = str(ROOT)
    env["EASEL_PYTHON"] = sys.executable
    proc = subprocess.run(command, cwd=str(scripts_dir.parent), env=env, capture_output=True, text=True, timeout=180, check=False)
    output = (proc.stdout or "") + (proc.stderr or "")
    return (output or f"Script exited with code {proc.returncode}.")[:MAX_RESULT]


def _update_profile_file(profile: str, filename: str, content: str) -> str:
    """Constrain profile enhancement writes to one known Markdown file in the selected profile."""
    if not re.fullmatch(r"[\w][\w-]{0,63}", profile, flags=re.UNICODE) or profile.startswith("_"): raise ValueError("invalid profile")
    if filename not in {"identity.md", "style.md", "audience.md", "platforms.md", "preferences.md", "memory.md"}:
        raise ValueError("profile file is not editable")
    if len(content.encode("utf-8")) > 24000: raise ValueError("profile text exceeds size limit")
    profile_root = _safe_under(ROOT / "profiles", profile)
    target = _safe_under(profile_root, filename)
    if target.parent != profile_root or not profile_root.is_dir() or not target.is_file(): raise ValueError("selected profile file does not exist")
    tmp = target.with_suffix(".md.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(target)
    return f"Updated profiles/{profile}/{filename}"


def execute_tool(name: str, args: dict[str, Any]) -> str:
    if name == "list_skills":
        return "\n".join(sorted(p.name for p in SKILLS.iterdir() if p.is_dir() and (p/"SKILL.md").is_file()))
    if name == "read_skill":
        skill = str(args.get("skill", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", skill): raise ValueError("invalid skill name")
        target = _safe_under(_safe_under(SKILLS, skill), str(args.get("file") or "SKILL.md"))
        if not target.is_file() or target.suffix.lower() not in {".md",".txt",".json"}: raise ValueError("skill text file not found")
        return target.read_text(encoding="utf-8")[:MAX_RESULT]
    if name in {"read_output", "write_output", "run_novel_check"}:
        target = _safe_under(OUTPUTS, str(args.get("path", "")))
        if name == "read_output":
            if not target.is_file() or target.stat().st_size > MAX_RESULT: raise ValueError("output file missing or too large")
            return target.read_text(encoding="utf-8")
        if name == "write_output":
            if target.suffix.lower() not in {".md",".txt",".json",".csv"}: raise ValueError("only text outputs can be written")
            content = str(args.get("content", ""))
            if len(content.encode()) > MAX_RESULT: raise ValueError("output exceeds size limit")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): raise ValueError("refusing to overwrite an existing output")
            target.write_text(content, encoding="utf-8")
            return "Wrote outputs/" + target.relative_to(OUTPUTS.resolve()).as_posix()
        if not target.is_file() or target.suffix.lower() not in {".md",".txt"}: raise ValueError("novel check requires .md/.txt under outputs/")
        script = SKILLS / "novel-writer" / "scripts" / "novel_ops.py"
        proc = subprocess.run([sys.executable,str(script),"slopcheck","-f",str(target)],cwd=ROOT,capture_output=True,text=True,timeout=30,check=False)
        return ((proc.stdout or "")+(proc.stderr or ""))[:MAX_RESULT]
    raise ValueError("tool is not allowed: " + name)

_SESSION_LOCKS: dict[str, Any] = {}
_SESSION_LOCKS_GUARD = __import__("threading").Lock()

def _session_lock(session_id: str):
    with _SESSION_LOCKS_GUARD:
        return _SESSION_LOCKS.setdefault(session_id, __import__("threading").RLock())

def _session_file(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)[:120] or "default"
    return STATE / "sessions" / (safe + ".json")

def _load(session_id: str):
    try:
        data=json.loads(_session_file(session_id).read_text(encoding="utf-8")); return data if isinstance(data,list) else []
    except (OSError,ValueError): return []

def _save(session_id: str, history):
    path=_session_file(session_id); path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    tmp=path.with_suffix(".tmp"); tmp.write_text(json.dumps(history[-80:],ensure_ascii=False),encoding="utf-8"); os.chmod(tmp,0o600); tmp.replace(path)

def delete_session(session_id: str) -> int:
    """Delete a session transcript and its profile-scoped variants."""
    base = _session_file(session_id)
    removed = 0
    candidates = [base]
    if base.parent.is_dir():
        candidates.extend(base.parent.glob(base.stem + "-profile-*.json"))
    for path in candidates:
        try:
            path.unlink()
            removed += 1
        except FileNotFoundError:
            pass
    return removed

def _system_prompt(persona):
    parts=[]
    for path in (ROOT/"prompts/SOUL.md",ROOT/"prompts/AGENTS.md"):
        if path.is_file(): parts.append(path.read_text(encoding="utf-8"))
    if persona:
        from easel.persona import load_profile_text
        profile=load_profile_text(persona)
        if profile: parts.append(f"当前画像「{persona}」资料，仅用于此画像会话：\n{profile}")
    parts.append("你在 Easel 原生运行时，先查并遵循技能。仅能使用提供的有限工具；仅能运行技能目录中的脚本，并必须等待用户逐次批准；脚本可能产生外部副作用。画像增强专用轮次只可修改已选画像内的既有六维 Markdown 文件。")
    return "\n\n".join(parts)

class AgentRuntime:
    def __init__(self, request: Callable[..., Any] | None = None, max_steps=12): self.request=request; self.max_steps=max_steps
    def _tool_schemas(self, profile_edit=None): return tool_schemas(profile_edit=bool(getattr(self, "_allow_profile_edit", False)) if profile_edit is None else profile_edit, script_execution=bool(getattr(self, "_allow_script_execution", True)))
    def _request(self, messages):
        if self.request: return self.request(messages=messages,tools=self._tool_schemas())
        base,key,model,protocol=provider_config()
        if protocol == "openai":
            r=httpx.post(base+"/chat/completions",json={"model":model or "gpt-4o","messages":messages,"tools":self._tool_schemas(),"tool_choice":"auto"},headers={"Authorization":f"Bearer {key}"},timeout=180); r.raise_for_status(); return r.json()
        system=next((m["content"] for m in messages if m["role"]=="system"),""); converted=[]
        for m in messages:
            if m["role"]=="system": continue
            if m["role"]=="tool": converted.append({"role":"user","content":[{"type":"tool_result","tool_use_id":m["tool_call_id"],"content":m["content"]}]})
            elif m["role"]=="assistant" and m.get("tool_calls"):
                converted.append({"role":"assistant","content":[{"type":"tool_use","id":c["id"],"name":c["function"]["name"],"input":json.loads(c["function"]["arguments"])} for c in m["tool_calls"]]})
            else: converted.append({"role":m["role"],"content":m["content"]})
        tools=[{"name":t["function"]["name"],"description":t["function"]["description"],"input_schema":t["function"]["parameters"]} for t in self._tool_schemas()]
        r=httpx.post(base+"/messages",json={"model":model,"max_tokens":8192,"system":system,"messages":converted,"tools":tools},headers={"x-api-key":key,"anthropic-version":os.getenv("EASEL_LLM_ANTHROPIC_VERSION","2023-06-01")},timeout=180); r.raise_for_status(); raw=r.json()
        calls=[]; text=[]
        for b in raw.get("content",[]):
            if b.get("type")=="text": text.append(b.get("text",""))
            elif b.get("type")=="tool_use": calls.append({"id":b["id"],"type":"function","function":{"name":b["name"],"arguments":json.dumps(b.get("input",{}))}})
        return {"choices":[{"message":{"role":"assistant","content":"".join(text),"tool_calls":calls}}]}
    def run(self,message,session_id="default",persona=None,cancel_event=None,allow_profile_edit=False,allow_script_execution=True)->Iterator[dict[str,str]]:
        scoped_id = session_id if not persona else f"{session_id}-profile-{persona}"
        with _session_lock(scoped_id):
            self._allow_profile_edit = bool(allow_profile_edit)
            self._allow_script_execution = bool(allow_script_execution)
            try:
                yield from self._run_session(message, session_id, persona, cancel_event, scoped_id, allow_profile_edit)
            finally:
                self._allow_profile_edit = False
                self._allow_script_execution = True

    def _run_session(self, message, session_id, persona, cancel_event, scoped_id, allow_profile_edit=False):
        history=_load(scoped_id)
        if not history or history[0].get("role")!="system": history=[{"role":"system","content":_system_prompt(persona)}]
        history.append({"role":"user","content":message})
        for _ in range(self.max_steps):
            if cancel_event is not None and cancel_event.is_set():
                answer="本轮已停止。"; history.append({"role":"assistant","content":answer}); _save(scoped_id,history)
                yield {"event":"token","data":answer}; yield {"event":"done","data":session_id}; return
            msg=self._request(history)["choices"][0]["message"]; calls=msg.get("tool_calls") or []
            if not calls:
                answer=msg.get("content") or ""; history.append({"role":"assistant","content":answer}); _save(scoped_id,history)
                if answer: yield {"event":"token","data":answer}
                yield {"event":"done","data":session_id}; return
            history.append(msg)
            for call in calls:
                fn=call.get("function",{}); name=fn.get("name","")
                try:
                    args=json.loads(fn.get("arguments") or "{}")
                    if name in {"ask_user", "run_skill_script"}:
                        from easel.native_settings import create_question, get_question
                    if name == "ask_user":
                        question=create_question(session_id,args.get("questions",[]))
                        yield {"event":"question","data":json.dumps(question,ensure_ascii=False)}
                        deadline=__import__("time").monotonic()+300
                        while __import__("time").monotonic()<deadline:
                            if cancel_event is not None and cancel_event.is_set(): break
                            state=get_question(session_id,question["id"])
                            if state and state.get("status")=="resolved": break
                            __import__("time").sleep(0.25)
                        result=json.dumps((state or {}).get("answers",{}),ensure_ascii=False) if state and state.get("status")=="resolved" else "User did not answer; ask with text in the next turn."
                    elif name == "run_skill_script" and not getattr(self, "_allow_script_execution", True):
                        result = "Script tools are disabled for this non-interactive runtime; use the interactive Easel chat to request approval."
                    elif name == "run_skill_script":
                        skill = str(args.get("skill", "")); script = str(args.get("script", "")); argv = args.get("args", [])
                        args_summary = json.dumps(argv if isinstance(argv, list) else [], ensure_ascii=False)[:1000]
                        options = [{"label": "运行一次", "description": "按以下参数运行。脚本可能读写文件、访问网络或调用外部服务。"}, {"label": "取消", "description": "不运行此脚本"}]
                        question=create_question(session_id,[{"questionId":"approval","header":"脚本运行审批","question":f"技能脚本：{skill}/scripts/{script}\n参数：{args_summary}\n允许运行吗？", "options":options}])
                        yield {"event":"question","data":json.dumps(question,ensure_ascii=False)}
                        deadline=__import__("time").monotonic()+300; state=None
                        while __import__("time").monotonic()<deadline:
                            if cancel_event is not None and cancel_event.is_set(): break
                            state=get_question(session_id,question["id"])
                            if state and state.get("status")=="resolved": break
                            __import__("time").sleep(0.25)
                        decision=(state or {}).get("answers",{}).get("approval", [])
                        if decision != ["运行一次"]: result="脚本运行已取消或审批超时。"
                        else: result=_execute_registered_skill_script(skill,script,argv)
                    elif name == "update_profile_file" and allow_profile_edit and persona:
                        result=_update_profile_file(persona, str(args.get("file", "")), str(args.get("content", "")))
                    else:
                        result=execute_tool(name,args)
                except Exception as exc: result=f"Tool error: {exc}"
                history.append({"role":"tool","tool_call_id":call.get("id",""),"content":result})
                yield {"event":"activity","data":f"执行工具：{name}"}
        answer="本轮已停止。" if cancel_event is not None and cancel_event.is_set() else "本轮工具调用达到安全步数上限。"; history.append({"role":"assistant","content":answer}); _save(scoped_id,history)
        yield {"event":"token","data":answer}; yield {"event":"done","data":session_id}
