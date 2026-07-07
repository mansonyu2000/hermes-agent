@echo off
:: say - Agent MQTT Send
:: Usage: say <to_uid> "message"
:: Shell: CMD / PowerShell / Git Bash all supported
where python >nul 2>&1
if %errorlevel% equ 0 (python "%~dp0say.py" %*) else (python3 "%~dp0say.py" %*)
