@echo off
rem Run Hermes with EXAONE env + SSL patch (submodule uv venv).
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\hermes-agent\run_hermes.cmd [hermes args...]
uv run --no-project --quiet python "%~dp0..\gallery.py" hermes %*
exit /b %ERRORLEVEL%
