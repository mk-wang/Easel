"""Check prerequisites for Easel's self-contained runtime."""
from __future__ import annotations
import os,shutil,sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[2]
GREEN="\033[0;32m"; RED="\033[0;31m"; YELLOW="\033[0;33m"; NC="\033[0m"
def _check(label,ok,detail=""):
    print(f"  {GREEN if ok else RED}{'OK' if ok else 'FAIL'}{NC} {label}")
    if not ok and detail: print(f"    └─ {detail}")
    return ok
def _python_ok(): return sys.version_info >= (3,10)
def _module_available(name):
    try: __import__(name); return True
    except ImportError: return False
def _env_configured():
    # Check process environment and .env names only; never print or persist credential values.
    values=dict(os.environ); path=PROJECT_ROOT/".env"
    if path.is_file():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line=line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key,value=line.split("=",1); values.setdefault(key.strip(),value.strip().strip('"').strip("'"))
        except OSError: pass
    def usable(k):
        v=values.get(k,"").strip()
        return bool(v) and "REPLACE_ME" not in v and not v.lower().startswith("your-")
    try:
        from easel.native_settings import load_config
        cfg = load_config()
        from easel.runtime import _usable_credential
        primary = cfg.get("providers", {}).get(cfg.get("primary", ""), {})
        selected_key = str(primary.get("key") or values.get(primary.get("credentialEnv", ""), ""))
        if primary.get("baseUrl") and _usable_credential(selected_key):
            return True
    except Exception:
        pass
    return (usable("EASEL_LLM_API_KEY") and usable("EASEL_LLM_BASE_URL")
            or usable("OPENAI_API_KEY") or usable("ANTHROPIC_API_KEY"))
def cmd_doctor(_args):
    print("Easel — 环境检查\n"); all_ok=True
    all_ok &= _check("Python >= 3.10",_python_ok(),"请安装 Python 3.10 或更高版本")
    all_ok &= _check("Python venv module",_module_available("venv"),"Debian/Ubuntu 请安装 python3-venv")
    for module in ("fastapi","uvicorn","sse_starlette","multipart","httpx"):
        all_ok &= _check(f"Python package: {module}",_module_available(module),"运行 pip install -e . 安装 Easel 依赖")
    node=shutil.which("node"); npm=shutil.which("npm")
    # Node/npm are only needed to rebuild the bundled frontend; a committed dist is runnable without them.
    frontend_ready=(PROJECT_ROOT/"web"/"frontend"/"dist"/"index.html").is_file()
    all_ok &= _check("Web frontend",frontend_ready or bool(node and npm),"运行 setup 脚本，或安装 Node.js/npm 后构建前端")
    skills=PROJECT_ROOT/"skills"/"openclaw"
    all_ok &= _check("Skill library",skills.is_dir() and any(skills.glob("*/SKILL.md")),"恢复 Easel 技能库目录")
    outputs=PROJECT_ROOT/"outputs"
    writable=outputs.is_dir() and os.access(outputs,os.W_OK)
    all_ok &= _check("Outputs directory",writable,"确保 outputs/ 可写")
    all_ok &= _check("Model provider configuration",_env_configured(),"配置 EASEL_LLM_API_KEY + EASEL_LLM_BASE_URL，OPENAI_API_KEY 或 ANTHROPIC_API_KEY")
    print()
    if all_ok: print(f"{GREEN}✓ 环境就绪{NC} — 运行 python -m easel ping 检查配置")
    else: print(f"{YELLOW}⚠ 有未满足项{NC} — 请按上述提示修复后重试")
    return 0 if all_ok else 1
