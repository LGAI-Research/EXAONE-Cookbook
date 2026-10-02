@echo off
rem Non-interactive browser-use + EXAONE demo orchestrator.
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\browser-use\run_cli_demo.cmd [--live]
uv run --no-project --quiet python "%~dp0..\gallery.py" demo browser-use %*
exit /b %ERRORLEVEL%
