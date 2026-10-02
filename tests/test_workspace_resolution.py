"""Regression coverage for native workspaces and removal of OpenClaw path probing."""
from pathlib import Path
import importlib.util
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_setup_installers_do_not_invoke_openclaw_or_sync_agent_workspaces():
    for path in (ROOT / "setup.sh", ROOT / "setup.ps1"):
        source = "\n".join(line for line in path.read_text(encoding="utf-8-sig").splitlines() if not line.lstrip().startswith("#"))
        assert "openclaw/sync.sh" not in source.lower()
        assert "openclaw config" not in source.lower()
        assert "Easel 不需要 OpenClaw" in source


def test_doctor_checks_bundled_skills_and_local_outputs_without_gateway():
    doctor = (ROOT / "easel" / "commands" / "doctor.py").read_text(encoding="utf-8")
    assert 'PROJECT_ROOT/"skills"/"openclaw"' in doctor  # bundled skill path
    assert '"outputs"' in doctor
    assert "openclaw_workspace" not in doctor and "gateway" not in doctor.lower()


def test_video_pipeline_outputs_under_checkout_not_openclaw_home():
    path = ROOT / "skills" / "openclaw" / "video-production" / "scripts" / "video_pipeline.py"
    spec = importlib.util.spec_from_file_location("video_pipeline_native_test", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert module._easel_root() == ROOT
    from argparse import Namespace
    module._easel_root = lambda: ROOT
    assert module.find_base(Namespace(base=str(Path("/tmp") / "easel-native-video-test"))) == Path("/tmp/easel-native-video-test")
    source = path.read_text(encoding="utf-8")
    assert ".openclaw" not in source


def test_active_runtime_entrypoints_have_no_openclaw_process_or_gateway_import():
    paths = [ROOT / "easel" / "runtime.py", ROOT / "easel" / "cli.py", ROOT / "easel" / "commands" / "doctor.py", ROOT / "easel" / "commands" / "ping.py", ROOT / "web" / "app.py"]
    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert "openclaw_base_cmd(" not in source
        assert "check_gateway(" not in source


def test_prompt_stack_is_owned_by_easel():
    assert (ROOT / "prompts" / "SOUL.md").is_file()
    assert (ROOT / "prompts" / "AGENTS.md").is_file()
    source = (ROOT / "easel" / "runtime.py").read_text(encoding="utf-8")
    assert 'ROOT/"prompts/SOUL.md"' in source


def test_setup_retains_optional_media_configuration_guidance():
    for path in (ROOT / "setup.sh", ROOT / "setup.ps1"):
        source = path.read_text(encoding="utf-8-sig")
        assert "媒体技能" in source
        assert ".env" in source
