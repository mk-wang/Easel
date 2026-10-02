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
    replies = iter([_tool_call("run_skill_script", {"skill":"mock-media", "script":"render.py", "args":[]}),
                    {"choices":[{"message":{"role":"assistant","content":"Rendered mock media.","tool_calls":[]}}]}])
    events = list(runtime.AgentRuntime(request=lambda **_: next(replies)).run("render", "approval-session"))
    approval = next(json.loads(e["data"]) for e in events if e["event"] == "question")
    assert "render.py" in approval["questions"][0]["question"]
    assert "MOCK_MEDIA" not in approval["questions"][0]["question"]
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
