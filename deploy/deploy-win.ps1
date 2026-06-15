# deploy-win.ps1 — Hermes Agent Windows 一键部署
# 用法: git pull 后在仓库根目录运行  .\deploy\deploy-win.ps1

$ErrorActionPreference = "Stop"
$SHARE = "\\192.168.3.23\projects\hermes-deploy"
$REPO = Split-Path -Parent $PSScriptRoot
$PYTHON = "C:\Python312"

Write-Host "=== Hermes Agent 部署 ===" -ForegroundColor Green

# 1. Python 3.12（从共享拷）
if (-not (Test-Path "$PYTHON\python.exe")) {
    Write-Host "[1/3] 复制 Python 3.12..." -ForegroundColor Yellow
    robocopy "$SHARE\python312" $PYTHON /E /NFL /NDL
    [Environment]::SetEnvironmentVariable('Path', "$PYTHON;$PYTHON\Scripts;" + [Environment]::GetEnvironmentVariable('Path', 'User'), 'User')
    Write-Host "  Python 3.12 就绪"
} else { Write-Host "[1/3] Python 3.12 已存在" }

# 2. 安装依赖
Write-Host "[2/3] pip install -e ..." -ForegroundColor Yellow
& "$PYTHON\python.exe" -m pip install -e $REPO --quiet

# 3. 自动升级钩子
Write-Host "[3/3] 注册升级监控(每10分钟)..." -ForegroundColor Yellow
$ACTION = New-ScheduledTaskAction -Execute "$PYTHON\python.exe" -Argument "$REPO\deploy\auto-upgrade.py"
$TRIGGER = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "HermesUpgrade" -Action $ACTION -Trigger $TRIGGER -RunLevel Highest -Force | Out-Null

Write-Host "=== 完成 ===`n启动: hermes" -ForegroundColor Green
