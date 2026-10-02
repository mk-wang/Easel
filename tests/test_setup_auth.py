"""Authentication/provider configuration regressions for the native Easel setup."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from easel import native_settings, runtime
from easel.commands import doctor


@pytest.mark.parametrize("value", ["", "REPLACE_ME", "sk-ant-REPLACE_ME", "your-api-key", "YOUR_API_KEY", "your_api_key"])
def test_placeholders_are_not_usable_credentials(value):
    assert runtime._usable_credential(value) is False


@pytest.mark.parametrize("value", ["sk-ant-testfake", "sk-proj-testfake", "local-adapter-token"])
def test_non_placeholder_credentials_remain_usable(value):
    assert runtime._usable_credential(value) is True


def test_doctor_recognizes_native_provider_and_rejects_placeholder(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(native_settings, "STATE", tmp_path / ".easel")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-testfake")
    native_settings.save_config({"primary":"openai", "providers":{"openai":{"baseUrl":"https://mock.test/v1", "model":"mock-model", "key":"", "credentialEnv":"OPENAI_API_KEY"}}})
    assert doctor._env_configured() is True
    monkeypatch.setenv("OPENAI_API_KEY", "sk-REPLACE_ME")
    assert doctor._env_configured() is False


def test_setup_scripts_do_not_require_or_write_openclaw_configuration():
    for path in (ROOT / "setup.sh", ROOT / "setup.ps1"):
        source = "\n".join(line for line in path.read_text(encoding="utf-8-sig").splitlines() if not line.lstrip().startswith("#"))
        assert "openclaw config set" not in source.lower()
        assert "openclaw/sync.sh" not in source.lower()
        assert "providers.json" in source or "Easel 不需要 OpenClaw" in source


def test_native_provider_file_is_private_and_does_not_store_placeholder(tmp_path, monkeypatch):
    monkeypatch.setattr(native_settings, "STATE", tmp_path / ".easel")
    native_settings.save_config({"primary":"openai", "providers":{"openai":{"key":"sk-mock"}}})
    path = native_settings.config_path()
    assert path.read_text(encoding="utf-8").find("sk-mock") >= 0
    assert os.stat(path).st_mode & 0o077 == 0
    assert runtime._usable_credential("sk-REPLACE_ME") is False
