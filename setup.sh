#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PROJECT_ROOT="$ROOT"
info(){ printf '[easel] %s\n' "$*"; }
ok(){ printf '[easel] OK: %s\n' "$*"; }
warn(){ printf '[easel] WARN: %s\n' "$*" >&2; }
step(){ printf '[easel] %s\n' "$*"; }
fail(){ printf '[easel] ERROR: %s\n' "$*" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || fail '需要 Python 3.10+。'
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || fail '需要 Python 3.10+。'
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  info '创建项目虚拟环境...'
  python3 -m venv "$ROOT/.venv" || fail '创建虚拟环境失败；请安装 Python venv 模块。'
fi
info '安装 Easel Python 依赖...'
# pip 镜像：EASEL_PIP_INDEX 指定 > 连通性探测 > 默认 PyPI；不修改全局 pip 配置。
PIP_INDEX="${EASEL_PIP_INDEX:-}"
PIP_INDEX_ARGS=()
if [ -z "$PIP_INDEX" ]; then
  if command -v timeout >/dev/null 2>&1; then
    if ! timeout 8 python3 -c "import urllib.request;urllib.request.urlopen('https://pypi.org/simple/', timeout=4)" >/dev/null 2>&1; then PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"; fi
  elif ! python3 -c "import urllib.request;urllib.request.urlopen('https://pypi.org/simple/', timeout=4)" >/dev/null 2>&1; then
    PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
  fi
fi
if [ -n "$PIP_INDEX" ]; then PIP_INDEX_ARGS=(-i "$PIP_INDEX"); warn "pip index: $PIP_INDEX"; else ok 'PyPI: pypi.org'; fi
PIP_ARGS=(install -e "$PROJECT_ROOT" --progress-bar on ${PIP_INDEX_ARGS[@]+"${PIP_INDEX_ARGS[@]}"})
if [ "$(id -u)" -eq 0 ]; then PIP_ARGS+=(--root-user-action=ignore); warn '当前以 root 安装'; fi
"$PY" -m pip install --upgrade pip "${PIP_INDEX_ARGS[@]}"
"$PY" -m pip "${PIP_ARGS[@]}"
if [ ! -f "$ROOT/.env" ]; then cp "$ROOT/.env.example" "$ROOT/.env"; info '已创建 .env；请按需填写模型服务配置。'; fi

# ---- 2. npm 源 ----
NPM_REGISTRY="${EASEL_NPM_REGISTRY:-}"
if [ -z "$NPM_REGISTRY" ]; then
  if npm ping --registry https://registry.npmjs.org --fetch-timeout=5000 --fetch-retries=0 --fetch-retry-mintimeout=0 >/dev/null 2>&1; then
    NPM_REGISTRY="https://registry.npmjs.org"; ok "npm registry: npmjs.org"
  else
    NPM_REGISTRY="https://registry.npmmirror.com"; warn "npmjs.org 不可达，切换到 npmmirror"
  fi
else ok "npm registry: ${NPM_REGISTRY}（EASEL_NPM_REGISTRY 指定）"; fi
NPM_REGISTRY_ARGS=(--registry "$NPM_REGISTRY")

# ---- 3. Easel Python dependencies ----
if [ -f "$ROOT/web/frontend/package-lock.json" ]; then
  if command -v npm >/dev/null 2>&1; then
    info '安装并构建 Web 前端...'
    (cd "$ROOT/web/frontend" && (npm ci --no-audit --no-fund --fetch-timeout=30000 --fetch-retries=1 "${NPM_REGISTRY_ARGS[@]}" || npm install --no-audit --no-fund --fetch-timeout=30000 --fetch-retries=1 "${NPM_REGISTRY_ARGS[@]}") && npm run build)
  elif [ ! -f "$ROOT/web/frontend/dist/index.html" ]; then
    fail '构建前端需要 Node.js/npm；安装后重新运行 setup.sh。'
  else info '未找到 npm，使用仓库内已有前端构建产物。'; fi
fi
if command -v ffmpeg >/dev/null 2>&1; then info "FFmpeg $(ffmpeg -version 2>&1 | head -1 | awk '{print $3}') 可用于媒体技能。"; else info 'FFmpeg 未安装；需要 FFmpeg 的媒体技能暂不可用。'; fi
"$PY" -m playwright install chromium
mkdir -p "$ROOT/outputs" "$ROOT/assets"
info '安装完成。启动：.venv/bin/easel web；检查：.venv/bin/easel doctor'
info '聊天模型可在 Web 设置中保存到 ~/.easel/providers.json；媒体技能可从项目 .env 读取可选配置。Easel 不需要 OpenClaw。'
