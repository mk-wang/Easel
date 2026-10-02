"""Native model configuration replaces OpenClaw-backed local CLI agent adapters."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))
from fastapi.testclient import TestClient
from easel import native_settings
import web.app as web


def test_legacy_local_agent_catalog_is_empty_and_native_provider_catalog_remains(tmp_path, monkeypatch):
    monkeypatch.setattr(native_settings, "STATE", tmp_path)
    native_settings.save_config({"primary":"openai", "providers":{"openai":{"baseUrl":"https://example.test/v1", "model":"mock", "key":"sk-mock", "protocol":"openai"}}})
    with TestClient(web.app, base_url="http://127.0.0.1:7860", headers={"Origin":"http://127.0.0.1:7860"}) as c:
        legacy = c.get("/api/settings/local-agents")
        native = c.get("/api/settings/models")
    assert legacy.status_code == 200 and legacy.json()["agents"] == []
    assert native.status_code == 200
    assert any(row["slot"] == "openai" for row in native.json()["channels"]["chat"]["rows"])


def test_retired_cli_adapter_endpoint_refuses_without_mutating_native_config(tmp_path, monkeypatch):
    monkeypatch.setattr(native_settings, "STATE", tmp_path)
    native_settings.save_config({"primary":"openai", "providers":{"openai":{"baseUrl":"https://example.test/v1", "model":"mock", "key":"sk-mock", "protocol":"openai"}}})
    before = native_settings.config_path().read_bytes()
    with TestClient(web.app, base_url="http://127.0.0.1:7860", headers={"Origin":"http://127.0.0.1:7860"}) as c:
        responses = [c.post("/api/settings/local-agents/enable", json={"id":agent})
                     for agent in ("claude-code", "gemini-cli", "codex", "opencode", "unknown")]
    assert all(response.status_code == 410 for response in responses)
    assert native_settings.config_path().read_bytes() == before
    assert all("Easel 原生 provider 配置" in response.json()["detail"] for response in responses)
