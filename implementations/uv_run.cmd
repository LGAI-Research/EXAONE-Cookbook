@echo off
rem Run a command in an implementation's isolated uv venv (separate from cookbook).
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\uv_run.cmd smolagents python run_agent.py
uv run --no-project --quiet python "%~dp0gallery.py" uv-run %*
exit /b %ERRORLEVEL%
