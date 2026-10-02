import asyncio
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "web"))
from easel import native_settings as settings, runtime
import app as web


def test_provider_config_load_save_masks_and_restricts_file_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STATE", tmp_path)
    settings.save_config({"primary": "proxy", "providers": {"proxy": {
        "baseUrl": "https://llm.example/v1", "model": "fake-model",
        "key": "secret-value", "protocol": "openai"}}})
    assert settings.load_config()["providers"]["proxy"]["key"] == "secret-value"
    assert settings.masked("secret-value") == "••••••alue"
    assert settings.config_path().stat().st_mode & 0o777 == 0o600
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    monkeypatch.delenv("EASEL_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("EASEL_LLM_API_KEY", raising=False)
    assert runtime.provider_config() == ("https://llm.example/v1", "secret-value", "fake-model", "openai")


def test_env_provider_fallback_does_not_need_openclaw(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STATE", tmp_path / "state")
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=fake-key\nOPENAI_BASE_URL=https://provider.example/v1\nOPENAI_MODEL=fake-model\n")
    for key in ("EASEL_LLM_BASE_URL", "EASEL_LLM_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    assert runtime.provider_config() == ("https://provider.example/v1", "fake-key", "fake-model", "openai")


def test_question_answer_is_session_bound_and_idempotent():
    settings._questions.clear()
    q = settings.create_question("s1", [{"questionId": "q1", "question": "Choose",
        "options": [{"label": "A"}, {"label": "B"}]}])
    assert settings.get_question("other", q["id"]) is None
    assert settings.answer_question("other", q["id"], {"q1": ["A"]})["ok"] is False
    assert settings.question_status("s1", [q["id"]])[q["id"]]["status"] == "pending"
    assert settings.answer_question("s1", q["id"], {"q1": ["X"]})["ok"] is True
    assert settings.question_status("s1", [q["id"]])[q["id"]]["status"] == "resolved"
    assert settings.answer_question("s1", q["id"], {"q1": ["A"]})["ok"] is False


def test_web_save_and_load_native_provider_without_openclaw(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STATE", tmp_path / "state")
    monkeypatch.setattr(web, "ENV_FILE", tmp_path / ".env")
    assert not hasattr(web, "_oc_config_path")  # Native settings never depend on an OpenClaw config path.
    req = web.ModelSaveRequest(channel="chat", rows=[web.ModelSaveRow(
        slot="custom", name="localproxy", model="fake-model", baseUrl="https://example.test/v1", key="fake-secret", primary=True)])
    result = asyncio.run(web.api_settings_models_save(req))
    assert result["ok"] is True
    assert settings.load_config()["primary"] == "localproxy"
    assert settings.load_config()["providers"]["localproxy"]["key"] == "fake-secret"
    rows = web._model_channels()["channels"]["chat"]["rows"]
    row = next(item for item in rows if item["name"] == "localproxy")
    assert row["keyMasked"].endswith("cret")
    assert "fake-secret" not in json.dumps(rows)
    assert not (tmp_path / "missing-openclaw.json").exists()


def test_question_http_contract_requires_originating_session():
    settings._questions.clear()
    q = settings.create_question("session-7", [{"questionId": "choice", "question": "Pick", "options": [{"label": "A"}]}])
    req = web.QuestionAnswerRequest(sessionId="wrong-session", questionId=q["id"], answers={"choice": ["A"]})
    assert asyncio.run(web.api_question_answer(req))["ok"] is False
    good = web.QuestionAnswerRequest(sessionId="session-7", questionId=q["id"], answers={"choice": ["custom response"]})
    assert asyncio.run(web.api_question_answer(good))["ok"] is True
    status = web.QuestionStatusRequest(sessionId="session-7", questionIds=[q["id"]])
    assert asyncio.run(web.api_question_status(status))["questions"][q["id"]]["status"] == "resolved"


def test_native_selected_provider_uses_legacy_credential_without_copying(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STATE", tmp_path / "state")
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=runtime-only-secret\n")
    settings.save_config({"primary": "openai", "providers": {"openai": {
        "baseUrl": "https://api.example/v1", "model": "test", "key": "",
        "protocol": "openai", "credentialEnv": "OPENAI_API_KEY"}}})
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert runtime.provider_config() == ("https://api.example/v1", "runtime-only-secret", "test", "openai")
    saved = json.loads(settings.config_path().read_text())
    assert saved["providers"]["openai"]["key"] == ""
