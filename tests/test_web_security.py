"""设置类接口的安全回归（PR #46/#47 引入的写 .env / 装工具入口）。

这些接口的特殊之处：`web/app.py` 监听 0.0.0.0 且无鉴权，而 `setup.sh` 会 `source .env` ——
所以「往 .env 写值」和「按 id 装工具」两条路径上的任何一点松动，都会直接变成命令执行或
Key 外泄。下面全是负向用例，配一条正向用例保证闸没修成谁都过不去。

运行：pytest tests/test_web_security.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "web"))
sys.path.insert(0, str(PROJECT_ROOT / "skills" / "shared" / "scripts"))

import app as web  # noqa: E402
import install_tool  # noqa: E402

ORIGINAL_ENV = (
    "OPENAI_BASE_URL=https://api.openai.com/v1\n"
    "OPENAI_API_KEY=sk-fake-not-a-real-key-for-test\n"
    "SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1\n"
    "SILICONFLOW_API_KEY=sk-fake-siliconflow-test-value\n"
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """把 .env 与 Easel 原生 provider store 隔离到临时目录。"""
    env_file = tmp_path / ".env"
    env_file.write_text(ORIGINAL_ENV, encoding="utf-8")
    monkeypatch.setattr(web, "ENV_FILE", env_file)
    from easel import native_settings
    monkeypatch.setattr(native_settings, "STATE", tmp_path / ".easel")
    native_settings.save_config({"primary": "openai", "providers": {
        "openai": {"baseUrl": "https://api.openai.com/v1", "model": "gpt-4o", "key": "sk-fake-existing", "protocol": "openai"},
        "myproxy": {"baseUrl": "https://good.example.com/v1", "model": "x", "key": "sk-fake-custom", "protocol": "openai"},
    }})
    # Redirect Path.home as an additional guard: tests must not touch real Easel state.
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    # local_write_guard 会把「非本机写请求」判 403。设置为本机来源。
    local = "http://127.0.0.1:7860"
    with TestClient(web.app, base_url=local, client=('127.0.0.1', 51234),
                    headers={'Origin': local}) as c:
        c.env_file = env_file          # 用例里用来断言「.env 一个字节都没变」
        c.native_state = native_settings.STATE
        c.native_config_before = (native_settings.config_path()).read_bytes()
        yield c


def _save(client, payload):
    return client.post("/api/settings/models/save", json=payload)


def _assert_blocked(client, payload):
    resp = _save(client, payload)
    assert resp.status_code >= 400, f"本该拒绝却放行了：{resp.status_code} {resp.text[:200]}"
    assert client.env_file.read_text(encoding="utf-8") == ORIGINAL_ENV, ".env 被改动了"
    from easel.native_settings import config_path
    assert config_path().read_bytes() == client.native_config_before, "provider store changed after rejected input"


# ---- .env 换行注入：值里塞一行 → setup.sh `source .env` 时被当命令执行 ----

@pytest.mark.parametrize("row", [
    {"slot": "openai", "model": "gpt-4o", "baseUrl": "https://api.openai.com/v1\nMALICIOUS=1"},
    {"slot": "openai", "model": "m\nEVIL=$(id)"},
    {"slot": "openai", "key": "sk-a\nPATH=/tmp"},
    {"slot": "openai", "key": "sk-a\rPATH=/tmp"},
])
def test_env_newline_injection_rejected(client, row):
    _assert_blocked(client, {"channel": "chat", "rows": [row]})


@pytest.mark.parametrize("updates", [
    {"OPENAI_API_KEY": "sk-x\nPATH=/tmp/evil"},   # 值里换行
    {"OPENAI_API_KEY": "sk-x\x00"},               # 值里 NUL
    {"A=B\nC": "1"},                              # 键名里换行
    {"FOO BAR": "1"},                             # 键名含空格
    {"9LIVES": "1"},                              # 键名数字开头
    {"": "1"},                                    # 空键名
])
def test_guard_env_values_rejects(updates):
    with pytest.raises(Exception):
        web._guard_env_values(updates)


# ---- 不换行也能执行命令：bash 在赋值右侧照做命令替换 ----
# `KEY=$(id)` 里没有任何换行，却在 `source .env` 时直接执行；`KEY=a;id` 则是元字符截断赋值
# 另起一条命令。只拦 \r\n\x00 等于没拦住这条路。
@pytest.mark.parametrize("value", [
    "sk-a$(id)",            # 命令替换
    "sk-a`id`",             # 反引号
    "sk-a${HOME}",          # 变量展开（值会被悄悄改写）
    "sk-a;id",              # 分号另起一条命令
    "sk-a&&id",
    "sk-a|id",
    "sk-a >/tmp/pwn",       # 空格 + 重定向
    "sk-a'\"",              # 引号：破坏后续解析
    "sk-a\\",               # 反斜杠续行
])
def test_guard_env_values_rejects_shell_metachars(value):
    with pytest.raises(Exception):
        web._guard_env_values({"OPENAI_API_KEY": value})


def test_env_shell_substitution_rejected_via_api(client):
    """走真接口也得拦住，且 .env 一个字节都不许变。"""
    _assert_blocked(client, {"channel": "chat",
                             "rows": [{"slot": "openai", "model": "gpt-4o", "key": "sk-a$(id)"}]})


def test_guard_env_values_allows_normal():
    web._guard_env_values({"OPENAI_API_KEY": "sk-normal", "OPENAI_BASE_URL": "https://a.com/v1"})


@pytest.mark.parametrize("value", [
    "sk-proj-Abc123_-xyz",                                   # 常见 key 形态
    "https://api.example.com/v1",                            # base url
    "https://gw.example.com:8443/openai/v1?api-version=1",   # 带端口与 query
    "anthropic/claude-sonnet-5",                             # 模型 id
    "8890",                                                  # 端口
    "a.b-c_d@e+f=g~h,i%j#k[l]",                              # 允许字符集全覆盖
])
def test_guard_env_values_allows_real_values(value):
    """收紧字符集不能把正常值一起误杀 —— 这几类是面板真会写进去的。"""
    web._guard_env_values({"OPENAI_API_KEY": value})


def test_both_env_writers_are_guarded():
    """两个写入口都得挂闸——漏一个等于没修。"""
    import inspect
    for fn in (web._write_env, web._write_env_direct):
        assert "_guard_env_values" in inspect.getsource(fn), fn.__name__


# ---- 换址窃 Key：改 Base URL + Key 留空（留空=沿用旧 Key）----

@pytest.mark.parametrize("channel,row", [
    ("chat", {"slot": "openai", "baseUrl": "https://evil.example.com/v1", "key": ""}),
    ("transcribe", {"slot": "siliconflow", "baseUrl": "https://evil.example.com/v1", "key": ""}),
    # 自定义供应商压根不写 .env，只有 openclaw.json 那侧的闸能拦
    ("chat", {"slot": "custom", "name": "myproxy", "model": "x",
              "baseUrl": "https://evil.example.com/v1", "key": ""}),
])
def test_rebase_without_new_key_rejected(client, channel, row):
    _assert_blocked(client, {"channel": channel, "rows": [row]})


def test_provider_base_change_requires_a_new_key(client):
    """A native provider key may not be redirected to a different endpoint while blank."""
    _assert_blocked(client, {"channel": "chat", "rows": [{"slot": "custom", "name": "myproxy", "model": "gpt-5.5", "baseUrl": "https://upstream.example.com/v1", "key": ""}]})


def test_local_gateway_helper():
    assert web._is_local_gateway_base("http://127.0.0.1:8890/v1")
    assert not web._is_local_gateway_base("https://api.openai.com/v1")
    assert not web._is_local_gateway_base("")
    assert not web._is_local_gateway_base(None)


# ---- Base URL 必须整串校验（只看开头挡不住内嵌凭据/控制字符）----

@pytest.mark.parametrize("bad", [
    "http://u:p@evil.example.com/v1",
    "ftp://evil.example.com",
    "https://api.openai.com/v1\tx",
    "javascript:alert(1)",
])
def test_base_url_validated_whole_string(client, bad):
    _assert_blocked(client, {"channel": "chat",
                             "rows": [{"slot": "openai", "baseUrl": bad, "key": "sk-new"}]})


@pytest.mark.parametrize("url,ok", [
    ("https://api.openai.com/v1", True),
    ("http://example.org:8080/v1", True),
    ("https://a.com\nX=1", False),
    ("http://u:p@evil.com", False),
    ("https://", False),
    ("not-a-url", False),
])
def test_valid_base_url(url, ok):
    assert web._valid_base_url(url) is ok


# ---- 自测探针会把真 Key 当 Bearer 发出去：不许指向本机/内网/云元数据 ----

@pytest.mark.parametrize("url", [
    "http://127.0.0.1:18789/v1",
    "http://localhost/v1",
    "http://169.254.169.254/latest",      # 云元数据
    "http://10.0.0.1/v1",
    "http://192.168.1.1/v1",
    "http://[::1]/v1",
    "http://no-such-host-zzz.invalid/v1",  # 解析不了就当不安全
])
def test_ssrf_guard_rejects_internal(url):
    assert web._ssrf_safe(url) is False


def test_selftest_probe_has_guards():
    import inspect
    src = inspect.getsource(web.api_models_selftest)
    assert "_valid_base_url" in src and "_ssrf_safe" in src, "探针前必须先过两道闸"
    assert "redirect_request" in src, "不能跟跳转——跟了等于绕过前面的判断"


# ---- 装工具接口：id 只认引擎里真实存在的配方 ----

@pytest.mark.parametrize("bad_id", ["--help", "; touch /tmp/pwn", "../../etc/passwd", "nope-xyz"])
def test_install_id_must_be_known(client, bad_id):
    assert client.post("/api/env/install", json={"id": bad_id}).status_code >= 400


def test_install_ids_come_from_engine():
    ids = web._install_tool_ids()
    assert ids and "node" in ids, f"配方表读不出来：{ids}"


# ---- 配方里的 {dir}：必须整元素落地，不可拼进更大的串（拼进去就能逃逸成代码）----

def test_fill_rejects_embedded_dir():
    with pytest.raises(ValueError):
        install_tool._fill(["--prefix={dir}/x"], "python3", "/tmp/a")


def test_fill_keeps_dir_intact():
    assert install_tool._fill(["{dir}"], "python3", "/tmp/a b'c") == ["/tmp/a b'c"]


# ---- 正向：别把闸修成谁都过不去 ----

def test_legit_save_still_works(client):
    resp = _save(client, {"channel": "chat", "rows": [
        {"slot": "openai", "model": "gpt-4o", "baseUrl": "https://new.example.com/v1", "key": "sk-fresh"}]})
    assert resp.status_code == 200, resp.text[:300]
    from easel.native_settings import load_config
    provider = load_config()["providers"]["openai"]
    assert provider["baseUrl"] == "https://new.example.com/v1"
    assert provider["key"] == "sk-fresh"
    assert client.env_file.read_text(encoding="utf-8") == ORIGINAL_ENV


def test_model_only_change_not_blocked(client):
    """A saved key is retained when only the model changes."""
    resp = _save(client, {"channel": "chat", "rows": [
        {"slot": "openai", "model": "gpt-4o-mini", "baseUrl": "https://api.openai.com/v1", "key": ""}]})
    assert resp.status_code == 200, resp.text[:300]
    from easel.native_settings import load_config
    assert load_config()["providers"]["openai"]["model"] == "gpt-4o-mini"
    assert load_config()["providers"]["openai"]["key"] == "sk-fake-existing"


def test_save_uses_only_easel_native_provider_store(client):
    assert not hasattr(web, "_oc_config_path")
    resp = _save(client, {"channel": "chat", "rows": [
        {"slot": "openai", "model": "deepseek-flash", "baseUrl": "https://api.deepseek.com", "key": "sk-fake-new"}]})
    assert resp.status_code == 200, resp.text[:300]
    from easel.native_settings import load_config
    assert load_config()["providers"]["openai"]["model"] == "deepseek-flash"


# ---- Native runtime: sessions, configuration, and stop behavior ----

def test_native_runtime_requires_provider_configuration(monkeypatch, tmp_path):
    from easel import native_settings
    from easel.runtime import AgentRuntime, RuntimeErrorBase
    monkeypatch.setattr(native_settings, "STATE", tmp_path / ".easel")
    native_settings.save_config({"primary": "openai", "providers": {}})
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("EASEL_LLM_API_KEY", raising=False)
    with pytest.raises(RuntimeErrorBase, match="未配置模型凭据"):
        AgentRuntime()._request([])


def test_native_runtime_sessions_are_isolated(tmp_path, monkeypatch):
    from easel import runtime
    monkeypatch.setattr(runtime, "STATE", tmp_path / ".easel")
    runtime._save("web-a", [{"role": "user", "content": "only a"}])
    runtime._save("web-b", [{"role": "user", "content": "only b"}])
    assert runtime._load("web-a")[0]["content"] == "only a"
    assert runtime._load("web-b")[0]["content"] == "only b"
    assert runtime._session_file("web-a") != runtime._session_file("web-b")


def test_native_runtime_profiles_use_separate_transcripts(tmp_path, monkeypatch):
    from easel import runtime
    monkeypatch.setattr(runtime, "STATE", tmp_path / ".easel")
    monkeypatch.setattr(runtime, "_system_prompt", lambda persona: "profile=" + str(persona))
    responses = iter([
        {"choices": [{"message": {"role": "assistant", "content": "general"}}]},
        {"choices": [{"message": {"role": "assistant", "content": "profile"}}]},
    ])
    agent = runtime.AgentRuntime(request=lambda **_: next(responses))
    list(agent.run("hi", "same-session"))
    list(agent.run("hi", "same-session", "writer"))
    general = runtime._load("same-session")
    profiled = runtime._load("same-session-profile-writer")
    assert general[0]["content"] == "profile=None"
    assert profiled[0]["content"] == "profile=writer"
    assert len(general) == len(profiled) == 3


def test_native_runtime_configuration_change_keeps_transcript(tmp_path, monkeypatch):
    from easel import runtime
    monkeypatch.setattr(runtime, "STATE", tmp_path / ".easel")
    history = [{"role": "user", "content": "earlier turn"}]
    runtime._save("stable-session", history)
    # Provider selection is deliberately outside the session filename and transcript.
    assert runtime._load("stable-session") == history
    assert runtime._session_file("stable-session").exists()


def test_native_stop_endpoint_sets_active_runtime_cancellation(client, monkeypatch):
    import threading
    flag = threading.Event()
    monkeypatch.setitem(web._RUNNING_CHAT, "active-session", flag)
    import asyncio
    result = asyncio.run(web.api_chat_stop(web.StopRequest(sessionId="active-session")))
    assert result == {"stopped": True}
    assert flag.is_set()
    web._RUNNING_CHAT.pop("active-session", None)


def test_native_sse_runtime_preserves_replay_contract():
    """The stream route uses the native runtime and persists per-turn replay events."""
    import inspect
    src = inspect.getsource(web.api_chat_stream)
    assert "AgentRuntime" in src
    assert "_job_event_file(turn_id)" in src
    assert '_save_turn(pk, "done"' in src


def test_native_sse_explicit_stop_sets_cancellation_flag():
    import inspect
    src = inspect.getsource(web.api_chat_stop)
    assert "flag.set()" in src
    assert "stopped" in src


def test_overlapping_web_chat_for_same_session_is_rejected(client, monkeypatch):
    import asyncio
    from fastapi import HTTPException
    from threading import Event
    session_id = "busy-session"
    monkeypatch.setitem(web._RUNNING_CHAT, session_id, Event())
    request = web.ChatRequest(message="second turn", sessionId=session_id)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(web.api_chat_stream(request))
    assert exc.value.status_code == 409
    web._RUNNING_CHAT.pop(session_id, None)


def test_primary_provider_rejects_placeholder_key(client):
    response = _save(client, {"channel":"chat", "rows":[{"slot":"openai", "model":"gpt-4o", "baseUrl":"https://api.openai.com/v1", "key":"sk-ant-REPLACE_ME", "primary":True}]})
    assert response.status_code == 400
    from easel.native_settings import load_config
    assert load_config()["providers"]["openai"]["key"] == "sk-fake-existing"
