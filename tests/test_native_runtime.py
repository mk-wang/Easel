import json
import pytest
from pathlib import Path

from easel import runtime


def test_native_tool_loop_persists_history_and_executes_skill(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path)
    events = []
    calls = iter([
        {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "function": {"name": "read_skill", "arguments": json.dumps({"skill": "novel-writer"})}}]}}]},
        {"choices": [{"message": {"role": "assistant", "content": "小说技能已加载。", "tool_calls": []}}]},
    ])
    agent = runtime.AgentRuntime(request=lambda **_: next(calls))
    events.extend(agent.run("帮我写小说", "novel-session"))
    assert [e["event"] for e in events] == ["activity", "token", "done"]
    history = json.loads((tmp_path / "sessions" / "novel-session.json").read_text())
    assert any(m.get("role") == "tool" and "黄金三章" in m.get("content", "") for m in history)


def test_provider_requests_enforce_cumulative_input_and_output_budgets_in_tool_loop(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path)
    monkeypatch.setattr(runtime, "provider_config", lambda: ("https://api.openai.com/v1", "redacted-test-token", "gpt-4o-mini", "openai"))
    replies=iter([
        {"choices":[{"message":{"role":"assistant","content":None,"tool_calls":[{"id":"1","function":{"name":"read_skill","arguments":json.dumps({"skill":"novel-writer"})}}]}}],"usage":{"prompt_tokens":100,"completion_tokens":120}},
        {"choices":[{"message":{"role":"assistant","content":"先定下主角目标和转折。","tool_calls":[]}}],"usage":{"prompt_tokens":200,"completion_tokens":180}},
    ])
    requests=[]

    class Response:
        def __init__(self, data): self.data=data
        def raise_for_status(self): pass
        def json(self): return self.data

    def post(url, *, content, headers, timeout):
        body=json.loads(content)
        requests.append((url,body))
        return Response(next(replies))

    monkeypatch.setattr(runtime.httpx,"post",post)
    agent=runtime.AgentRuntime(max_steps=4,max_completion_tokens=200,
                               max_total_input_tokens=300000,max_total_output_tokens=300)
    events=list(agent.run("给我一个小说写作方法", "budgeted-novel-session", allow_script_execution=False))
    assert len(requests)==2
    assert [body["max_completion_tokens"] for _,body in requests]==[200,180]
    assert all(url=="https://api.openai.com/v1/chat/completions" for url,_ in requests)
    assert events[-1]=={"event":"done","data":"budgeted-novel-session"}
    # OpenAI's official gpt-4o-mini standard rates: $0.15/M input, $0.60/M output.
    # Defaults reserve at most 300k conservative input tokens and 2,048 output tokens.
    default_cost_bound=(300000*0.15 + 2048*0.60)/1_000_000
    assert default_cost_bound < 0.10
    hard_cost_bound=(400000*0.15 + 8192*0.60)/1_000_000
    assert hard_cost_bound < 0.10
    test_cost_bound=(300000*0.15 + 300*0.60)/1_000_000
    assert test_cost_bound < 0.10


def test_total_input_budget_stops_before_second_provider_request(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path)
    monkeypatch.setattr(runtime, "provider_config", lambda: ("https://api.openai.com/v1", "redacted-test-token", "gpt-4o-mini", "openai"))
    initial_messages=[{"role":"system","content":runtime._system_prompt(None)},
                      {"role":"user","content":"先读取小说写作技能"}]
    first_body={"model":"gpt-4o-mini","messages":initial_messages,"tools":runtime.tool_schemas(script_execution=False),
                "tool_choice":"auto","max_completion_tokens":512}
    input_budget=runtime.AgentRuntime._input_token_upper_bound(
        json.dumps(first_body,ensure_ascii=False,separators=(",",":")).encode("utf-8")) + 1
    calls=[]

    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"choices":[{"message":{"role":"assistant","content":None,"tool_calls":[{"id":"read","function":{"name":"read_skill","arguments":json.dumps({"skill":"novel-writer"})}}]}}],"usage":{"prompt_tokens":1,"completion_tokens":1}}

    def post(url, *, content, headers, timeout):
        calls.append(json.loads(content))
        return Response()

    monkeypatch.setattr(runtime.httpx,"post",post)
    agent=runtime.AgentRuntime(max_completion_tokens=512,max_total_input_tokens=input_budget,
                               max_total_output_tokens=2048)
    events=list(agent.run("先读取小说写作技能", "input-budget-session", allow_script_execution=False))
    assert len(calls)==1
    assert "输入预算已用尽" in events[-2]["data"]
    assert events[-1]=={"event":"done","data":"input-budget-session"}


def test_tools_reject_traversal_and_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "OUTPUTS", tmp_path / "outputs")
    runtime.OUTPUTS.mkdir()
    try:
        runtime.execute_tool("write_output", {"path": "../escape.md", "content": "x"})
        assert False, "traversal must fail"
    except ValueError:
        pass
    target = runtime.OUTPUTS / "book" / "chapter.md"
    target.parent.mkdir(); target.write_text("existing")
    try:
        runtime.execute_tool("write_output", {"path": "book/chapter.md", "content": "new"})
        assert False, "overwrite must fail"
    except ValueError:
        pass
    assert target.read_text() == "existing"


def test_runtime_exposes_only_bounded_script_runner_and_no_generic_executor():
    names = {schema["function"]["name"] for schema in runtime.tool_schemas()}
    assert "run_skill_script" in names
    assert "run_shell" not in names and "run_command" not in names
    with pytest.raises(ValueError):
        runtime.execute_tool("run_skill_script", {"skill": "novel-writer", "script": "novel_ops.py", "args": ["--help"]})


def test_video_pipeline_default_outputs_under_easel_checkout():
    script = runtime.ROOT / "skills" / "openclaw" / "video-production" / "scripts" / "video_pipeline.py"
    namespace = {"__file__": str(script)}
    exec(compile(script.read_text(encoding="utf-8"), str(script), "exec"), namespace)
    assert namespace["_easel_root"]() == runtime.ROOT


def test_delete_session_removes_profile_scoped_transcripts(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path)
    runtime._save("web-session", [{"role": "user", "content": "general"}])
    runtime._save("web-session-profile-writer", [{"role": "user", "content": "profile"}])
    assert runtime.delete_session("web-session") == 2
    assert runtime._load("web-session") == []
    assert runtime._load("web-session-profile-writer") == []


def test_same_session_turns_are_serialized_without_losing_history(tmp_path, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    monkeypatch.setattr(runtime, "STATE", tmp_path)
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()
    snapshots = []
    calls = 0
    call_guard = threading.Lock()

    def request(messages, tools):
        nonlocal calls
        with call_guard:
            calls += 1
            current = calls
        snapshots.append([m.get("content") for m in messages])
        if current == 1:
            first_entered.set()
            assert release_first.wait(2)
        else:
            second_entered.set()
        return {"choices": [{"message": {"role": "assistant", "content": f"answer-{current}"}}]}

    agent = runtime.AgentRuntime(request=request)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(lambda: list(agent.run("first", "shared-session")))
        assert first_entered.wait(1)
        second = pool.submit(lambda: list(agent.run("second", "shared-session")))
        assert not second_entered.wait(0.1), "a second request entered the provider before the first transcript was saved"
        release_first.set()
        first.result(timeout=2); second.result(timeout=2)
    assert second_entered.is_set()
    assert any("first" in snapshot and "answer-1" in snapshot and "second" in snapshot for snapshot in snapshots)
    assert len([m for m in runtime._load("shared-session") if m.get("role") == "user"]) == 2


def test_provider_config_rejects_placeholder_credentials(tmp_path, monkeypatch):
    from easel import native_settings
    from easel.runtime import RuntimeErrorBase, provider_config
    monkeypatch.setattr(native_settings, "STATE", tmp_path / ".easel")
    native_settings.save_config({"primary": "anthropic", "providers": {
        "anthropic": {"baseUrl": "https://api.anthropic.com/v1", "key": "sk-ant-REPLACE_ME", "model": "claude-sonnet-4-6", "protocol": "anthropic"},
    }})
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "EASEL_LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeErrorBase, match="API Key"):
        provider_config()


def _tool_call(name, args, call_id="1"):
    return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
        {"id": call_id, "function": {"name": name, "arguments": json.dumps(args)}}]}}]}


def test_registered_media_script_runs_only_after_explicit_approval(tmp_path, monkeypatch):
    from easel import native_settings
    monkeypatch.setattr(runtime, "STATE", tmp_path / "state")
    skill = tmp_path / "skills" / "mock-media"; (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "render.py").write_text("print('MOCK_MEDIA_RENDER_OK')", encoding="utf-8")
    monkeypatch.setattr(runtime, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(native_settings, "create_question", lambda sid, qs: {"id": "approval-1", "sessionId": sid, "questions": qs, "status": "pending"})
    monkeypatch.setattr(native_settings, "get_question", lambda sid, qid: {"id": qid, "status": "resolved", "answers": {"approval": ["运行一次"]}})
    replies = iter([_tool_call("run_skill_script", {"skill":"mock-media", "script":"render.py", "args":["--mock", "visible-tail"]}),
                    {"choices":[{"message":{"role":"assistant","content":"Rendered mock media.","tool_calls":[]}}]}])
    events = list(runtime.AgentRuntime(request=lambda **_: next(replies)).run("render", "approval-session"))
    approval = next(json.loads(e["data"]) for e in events if e["event"] == "question")
    approval_text = approval["questions"][0]["question"]
    assert "render.py" in approval_text
    assert "visible-tail" in approval_text
    assert "MOCK_MEDIA" not in approval_text
    history = runtime._load("approval-session")
    assert any("MOCK_MEDIA_RENDER_OK" in m.get("content", "") for m in history if m.get("role") == "tool")


def test_registered_script_approval_cancelled_never_starts_process(tmp_path, monkeypatch):
    from easel import native_settings
    monkeypatch.setattr(runtime, "STATE", tmp_path / "state")
    monkeypatch.setattr(native_settings, "create_question", lambda sid, qs: {"id":"approval-2", "sessionId":sid,"questions":qs,"status":"pending"})
    monkeypatch.setattr(native_settings, "get_question", lambda sid, qid: {"id":qid,"status":"resolved","answers":{"approval":["取消"]}})
    monkeypatch.setattr(runtime, "_execute_registered_skill_script", lambda *a: pytest.fail("cancelled script must not execute"))
    replies = iter([_tool_call("run_skill_script", {"skill":"skill-wechat-publisher", "script":"publish.py", "args":["--publish"]}),
                    {"choices":[{"message":{"role":"assistant","content":"Cancelled.","tool_calls":[]}}]}])
    list(runtime.AgentRuntime(request=lambda **_: next(replies)).run("publish", "cancel-session"))
    assert any("取消" in m.get("content", "") for m in runtime._load("cancel-session") if m.get("role") == "tool")


def test_script_runner_rejects_shell_and_path_traversal(tmp_path, monkeypatch):
    root = tmp_path / "skills"; scripts = root / "mock" / "scripts"; scripts.mkdir(parents=True)
    (scripts / "go.sh").write_text("echo unsafe", encoding="utf-8")
    monkeypatch.setattr(runtime, "SKILLS", root)
    with pytest.raises(ValueError): runtime._execute_registered_skill_script("mock", "go.sh", [])
    with pytest.raises(ValueError): runtime._execute_registered_skill_script("mock", "../outside.py", [])


def test_profile_edit_tool_is_scoped_and_changes_existing_selected_file(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    profile = tmp_path / "profiles" / "创作者"; profile.mkdir(parents=True)
    (profile / "style.md").write_text("baseline", encoding="utf-8")
    assert "update_profile_file" not in {x["function"]["name"] for x in runtime.tool_schemas()}
    assert runtime._update_profile_file("创作者", "style.md", "updated style") == "Updated profiles/创作者/style.md"
    assert (profile / "style.md").read_text() == "updated style"
    with pytest.raises(ValueError): runtime._update_profile_file("创作者", "../../secret.md", "bad")
    with pytest.raises(ValueError): runtime._update_profile_file("创作者", "notes.txt", "bad")


def test_profile_enhancement_tool_only_offered_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path / "state")
    observed = []
    def request(messages, tools):
        observed.append({t["function"]["name"] for t in tools})
        return {"choices":[{"message":{"role":"assistant","content":"ok","tool_calls":[]}}]}
    list(runtime.AgentRuntime(request=request).run("enhance", "p1", "writer", allow_profile_edit=True))
    assert "update_profile_file" in observed[0]


def test_profile_build_uses_scoped_profile_tool_and_marks_done_after_change(tmp_path, monkeypatch):
    import time
    import sys
    sys.path.insert(0, str(runtime.ROOT / "web"))
    import app as web
    profile_root = tmp_path / "profiles"
    state_root = tmp_path / "state"
    monkeypatch.setattr(web, "PROFILES_DIR", profile_root)
    monkeypatch.setattr(web, "PROFILE_BUILD_DIR", state_root / "_profile_build")
    monkeypatch.setattr(runtime, "ROOT", tmp_path)

    native_agent = runtime.AgentRuntime
    monkeypatch.setattr(runtime, "STATE", state_root / "sessions")
    class MockAgent:
        def run(self, message, session_id, persona, allow_profile_edit=False, **kwargs):
            assert allow_profile_edit is True and kwargs.get("allow_script_execution") is False
            replies = iter([_tool_call("update_profile_file", {"file":"style.md", "content":"AI-enhanced style"}),
                            {"choices":[{"message":{"role":"assistant", "content":"已补全画像风格。", "tool_calls":[]}}]}])
            yield from native_agent(request=lambda **_: next(replies)).run(
                message, session_id, persona, allow_profile_edit=allow_profile_edit,
                allow_script_execution=False)
    monkeypatch.setattr(runtime, "AgentRuntime", MockAgent)
    from fastapi.testclient import TestClient
    with TestClient(web.app, base_url="http://127.0.0.1:7860", headers={"Origin":"http://127.0.0.1:7860"}) as client:
        created = client.post("/api/profile/build", json={"name":"writer", "form":{"direction":"fiction"}})
        assert created.status_code == 200
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            status = client.get("/api/profile/build/status/writer").json()
            if status["state"] != "running": break
            time.sleep(0.02)
        assert status["state"] == "done", status
    assert (profile_root / "writer" / "style.md").read_text(encoding="utf-8") == "AI-enhanced style"


def test_oversize_approval_payload_is_rejected_instead_of_truncated(tmp_path, monkeypatch):
    from easel import native_settings
    monkeypatch.setattr(runtime, "STATE", tmp_path / "state")
    skill = tmp_path / "skills" / "mock"; (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("print('should not run')", encoding="utf-8")
    monkeypatch.setattr(runtime, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(native_settings, "create_question", lambda *a: pytest.fail("oversize approval must not be displayed"))
    monkeypatch.setattr(runtime, "_execute_registered_skill_script", lambda *a, **k: pytest.fail("oversize script must not run"))
    args = {"skill":"mock", "script":"run.py", "args":["x" * 1000, "TRAILING_SECRET_ARGUMENT"]}
    replies = iter([_tool_call("run_skill_script", args), {"choices":[{"message":{"role":"assistant","content":"Rejected safely.","tool_calls":[]}}]}])
    events = list(runtime.AgentRuntime(request=lambda **_: next(replies), max_completion_tokens=2048,
                                       max_total_output_tokens=8192).run("run", "oversize-session"))
    assert not any(e["event"] == "question" for e in events)
    tool_result = next(m["content"] for m in runtime._load("oversize-session") if m.get("role") == "tool")
    assert "完整脚本参数无法放入审批卡" in tool_result


def test_script_runner_cancel_before_launch_does_not_spawn(tmp_path, monkeypatch):
    import threading
    root = tmp_path / "skills"; scripts = root / "mock" / "scripts"; scripts.mkdir(parents=True)
    marker = tmp_path / "ran"
    (scripts / "run.py").write_text(f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')", encoding="utf-8")
    monkeypatch.setattr(runtime, "SKILLS", root)
    event = threading.Event(); event.set()
    result = runtime._execute_registered_skill_script("mock", "run.py", [], cancel_event=event)
    assert "before launch" in result
    assert not marker.exists()


@pytest.mark.skipif(__import__("os").name != "posix", reason="process-group child cleanup is validated on POSIX")
def test_script_runner_cancellation_stops_child_process_tree(tmp_path, monkeypatch):
    import os
    import threading
    import time
    root = tmp_path / "skills"; scripts = root / "mock" / "scripts"; scripts.mkdir(parents=True)
    pid_file = tmp_path / "child.pid"; marker = tmp_path / "child-terminated"; ready = tmp_path / "child-ready"
    child_code = ("import pathlib,signal,sys,time; p=pathlib.Path(sys.argv[1]); ready=pathlib.Path(sys.argv[2]); "
                  "signal.signal(signal.SIGTERM,lambda *_:p.write_text('terminated')); ready.write_text('ready'); time.sleep(30)")
    script = scripts / "run.py"
    script.write_text("import subprocess,sys,time,pathlib\n"
                      f"child=subprocess.Popen([sys.executable,'-c',{child_code!r},{str(marker)!r},{str(ready)!r}])\n"
                      f"pathlib.Path({str(pid_file)!r}).write_text(str(child.pid))\n"
                      "time.sleep(30)\n", encoding="utf-8")
    from easel import native_settings
    monkeypatch.setattr(runtime, "SKILLS", root)
    monkeypatch.setattr(runtime, "STATE", tmp_path / "state")
    monkeypatch.setattr(native_settings, "create_question", lambda sid, qs: {"id":"q-cancel", "sessionId":sid, "questions":qs, "status":"pending"})
    monkeypatch.setattr(native_settings, "get_question", lambda sid, qid: {"id":qid, "status":"resolved", "answers":{"approval":["运行一次"]}})
    cancel = threading.Event(); events = []
    replies = iter([_tool_call("run_skill_script", {"skill":"mock", "script":"run.py", "args":[]}),
                    {"choices":[{"message":{"role":"assistant", "content":"done", "tool_calls":[]}}]}])
    agent = runtime.AgentRuntime(request=lambda **_: next(replies))
    worker = threading.Thread(target=lambda: events.extend(agent.run("run", "tree-cancel", cancel_event=cancel)))
    worker.start()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not pid_file.exists(): time.sleep(0.02)
    assert pid_file.is_file(), "mock child never started"
    child_pid = int(pid_file.read_text())
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not ready.exists(): time.sleep(0.02)
    assert ready.is_file(), "mock child did not install its termination handler"
    cancel.set(); worker.join(timeout=5)
    assert not worker.is_alive(), "cancel did not return promptly"
    assert any(e.get("event") == "token" and "已停止" in e.get("data", "") for e in events)
    assert any("canceled" in m.get("content", "").lower() for m in runtime._load("tree-cancel") if m.get("role") == "tool")
    assert marker.read_text() == "terminated"
    with pytest.raises(ProcessLookupError): os.kill(child_pid, 0)


def test_cli_question_answer_does_not_replace_selected_persona(monkeypatch, capsys):
    import builtins
    from easel import cli
    from easel.native_settings import create_question
    monkeypatch.setattr(cli, "_list_personas", lambda: ["writer"])
    inputs = iter(["1", "first turn", "1", "second turn", "/quit"])
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(inputs))
    seen = []
    class FakeAgent:
        def run(self, message, session_id, persona=None, **kwargs):
            seen.append((message, persona))
            if message == "first turn":
                card = create_question(session_id, [{"questionId":"continue", "question":"Continue?", "options":[{"label":"继续"}, {"label":"取消"}]}])
                yield {"event":"question", "data":json.dumps(card,ensure_ascii=False)}
            yield {"event":"token", "data":"ok"}
    monkeypatch.setattr("easel.runtime.AgentRuntime", FakeAgent)
    assert cli.cmd_chat(None) == 0
    assert seen == [("first turn", "writer"), ("second turn", "writer")]
