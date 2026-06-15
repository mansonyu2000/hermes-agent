# deploy-win.ps1 — Hermes + WinPeek 开发机一键部署
# 用法: git pull 后在仓库根目录运行  .\deploy\deploy-win.ps1

$ErrorActionPreference = "Stop"
$SHARE = "\\192.168.3.23\projects\hermes-deploy"
$HERMES = Split-Path -Parent $PSScriptRoot
$PYTHON = "C:\Python312"
$WORK = "D:\mydata\mycode\github"
$WINPEEK = "$WORK\winpeek-prod"

Write-Host "=== Hermes + WinPeek 开发机部署 ===" -ForegroundColor Green

# 1. Python 3.12
if (-not (Test-Path "$PYTHON\python.exe")) {
    Write-Host "[1/5] Python 3.12..." -ForegroundColor Yellow
    robocopy "$SHARE\python312" $PYTHON /E /NFL /NDL
    [Environment]::SetEnvironmentVariable('Path', "$PYTHON;$PYTHON\Scripts;" + [Environment]::GetEnvironmentVariable('Path', 'User'), 'User')
} else { Write-Host "[1/5] Python 3.12 OK" }

# 2. WinPeek-prod
Write-Host "[2/5] WinPeek-prod..." -ForegroundColor Yellow
if (-not (Test-Path $WINPEEK)) {
    mkdir -Force $WORK | Out-Null
    git clone http://gitlab.test.com:8080/mansonyu/PeekabooWin.git $WINPEEK
} else {
    cd $WINPEEK; git pull origin prod
}

# 3. Hermes 依赖
Write-Host "[3/5] pip install hermes..." -ForegroundColor Yellow
& "$PYTHON\python.exe" -m pip install -e $HERMES --quiet

# 4. WinPeek 依赖
Write-Host "[4/5] pip install winpeek-say..." -ForegroundColor Yellow
& "$PYTHON\python.exe" -m pip install -e $WINPEEK\bin --quiet

# 5. 开机自启 + 升级钩子
Write-Host "[5/5] 注册自启..." -ForegroundColor Yellow

# 升级监控 (每10分钟)
$A1 = New-ScheduledTaskAction -Execute "$PYTHON\python.exe" -Argument "$HERMES\deploy\auto-upgrade.py"
$T1 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "HermesUpgrade" -Action $A1 -Trigger $T1 -RunLevel Highest -Force | Out-Null

Write-Host "=== 部署完成 ===" -ForegroundColor Green
Write-Host "Hermes:  hermes"
Write-Host "WinPeek: cd $WINPEEK"
