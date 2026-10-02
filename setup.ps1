# Easel setup for Windows PowerShell 5.1+.
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Split-Path -Parent $MyInvocation.MyCommand.Path)).Path
$Venv = Join-Path $Root '.venv'
$Python = Join-Path $Venv 'Scripts\python.exe'
function Info($Message) { Write-Host "[easel] $Message" -ForegroundColor Cyan }
function Fail($Message) { Write-Error $Message; exit 1 }
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { $pythonCommand = Get-Command py -ErrorAction SilentlyContinue }
if (-not $pythonCommand) { Fail '需要 Python 3.10+。' }
$pythonArgs = @()
if ($pythonCommand.Name -eq 'py.exe' -or $pythonCommand.Name -eq 'py') { $pythonArgs = @('-3') }
& $pythonCommand.Source @pythonArgs -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)'
if ($LASTEXITCODE -ne 0) { Fail '需要 Python 3.10+。' }
if (-not (Test-Path $Python)) { Info '创建 Python 虚拟环境...'; & $pythonCommand.Source @pythonArgs -m venv $Venv; if ($LASTEXITCODE -ne 0) { Fail '创建虚拟环境失败；请确认 Python venv 可用。' } }
Info '安装 Easel Python 依赖...'
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail 'pip 升级失败。' }
& $Python -m pip install -e $Root
if ($LASTEXITCODE -ne 0) { Fail 'Easel Python 依赖安装失败。' }
$envFile = Join-Path $Root '.env'
if (-not (Test-Path $envFile)) { Copy-Item (Join-Path $Root '.env.example') $envFile; Info '已创建 .env；请按需填写模型服务配置。' }
$Frontend = Join-Path $Root 'web\frontend'
if (Test-Path (Join-Path $Frontend 'package-lock.json')) {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Info '安装并构建 Web 前端...'
        Push-Location $Frontend
        try { & npm ci; if ($LASTEXITCODE -ne 0) { Fail '前端依赖安装失败。' }; & npm run build; if ($LASTEXITCODE -ne 0) { Fail '前端构建失败。' } }
        finally { Pop-Location }
    } elseif (-not (Test-Path (Join-Path $Frontend 'dist\index.html'))) { Fail '构建前端需要 Node.js/npm；安装后重新运行 setup.ps1。' }
    else { Info '未找到 npm，使用仓库内已有前端构建产物。' }
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Info 'FFmpeg 未安装；需要 FFmpeg 的媒体技能暂不可用。' }
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'outputs'),(Join-Path $Root 'assets') | Out-Null
Info '安装完成。启动：.venv\Scripts\easel.exe web；检查：.venv\Scripts\easel.exe doctor'
Info '聊天模型可在 Web 设置中保存到 ~/.easel/providers.json；媒体技能可从项目 .env 读取可选配置。Easel 不需要 OpenClaw。'
