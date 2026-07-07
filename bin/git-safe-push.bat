@echo off
REM git-safe-push — blocks GitHub pushes, guides to gitlab-push
setlocal enabledelayedexpansion

set REMOTE=%1
set BRANCH=%2

if /i "%REMOTE%"=="origin" ( call :block_github & exit /b 1 )
if /i "%REMOTE%"=="github" ( call :block_github & exit /b 1 )

for /f "tokens=*" %%r in ('git remote get-url %REMOTE% 2^>nul') do set URL=%%r
echo !URL! | findstr /i "github.com" >nul
if !errorlevel! equ 0 ( call :block_github & exit /b 1 )

git push %*
exit /b %errorlevel%

:block_github
echo.
echo ╔══════════════════════════════════════════╗
echo ║  ❌ 不能推送到 GitHub！                   ║
echo ║  正确：git push local %BRANCH%             ║
echo ╚══════════════════════════════════════════╝
echo.
exit /b 1
