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


def test_runtime_does_not_expose_arbitrary_skill_script_execution():
    assert all(schema["function"]["name"] != "run_skill_script" for schema in runtime.tool_schemas())
    try:
        runtime.execute_tool("run_skill_script", {"skill": "novel-writer", "script": "novel_ops.py", "args": ["--help"]})
        assert False, "arbitrary script execution must not be exposed"
    except ValueError:
        pass


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
