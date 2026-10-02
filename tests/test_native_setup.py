from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_installers_do_not_require_or_configure_openclaw():
    for name in ('setup.sh', 'setup.ps1'):
        source = (ROOT / name).read_text(encoding='utf-8-sig').lower()
        assert 'npm install -g openclaw' not in source
        assert '.openclaw' not in source
        assert 'npm install -g' not in source

def test_cli_has_no_gateway_or_openclaw_dependency():
    source = (ROOT / 'easel' / 'cli.py').read_text(encoding='utf-8').lower()
    assert 'openclaw' not in source
    assert 'gateway' not in source
    assert 'agentruntime' in source
