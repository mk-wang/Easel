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


def test_clean_home_path_smoke_with_mock_openai_and_no_openclaw(tmp_path):
    import http.server
    import json
    import os
    import subprocess
    import threading
    import sys
    from easel.persona import list_personas
    from easel import runtime

    class Handler(http.server.BaseHTTPRequestHandler):
        requests = 0
        def do_POST(self):
            Handler.requests += 1
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            body = json.dumps({"choices":[{"message":{"role":"assistant","content":"mock-runtime-response","tool_calls":[]}}]}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *_): pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        empty_path = tmp_path / "bin"; empty_path.mkdir()
        env = {"HOME":str(tmp_path / "home"), "PATH":str(empty_path), "PYTHONPATH":str(runtime.ROOT),
               "EASEL_STATE_DIR":str(tmp_path / "state"), "OPENAI_API_KEY":"sk-test-fake",
               "OPENAI_BASE_URL":f"http://127.0.0.1:{server.server_address[1]}/v1", "OPENAI_MODEL":"mock-model", "EASEL_LLM_BASE_URL":"", "EASEL_LLM_API_KEY":"", "ANTHROPIC_API_KEY":""}
        (tmp_path / "home").mkdir()
        prompt = ("0\n" if list_personas() else "") + "hello\n/quit\n"
        proc = subprocess.run([sys.executable, "-m", "easel", "chat"], input=prompt, text=True,
                              capture_output=True, env=env, cwd=runtime.ROOT, timeout=15)
        assert proc.returncode == 0, proc.stderr
        assert "mock-runtime-response" in proc.stdout
        assert Handler.requests == 1
        assert list((tmp_path / "state" / "sessions").glob("*.json"))
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
