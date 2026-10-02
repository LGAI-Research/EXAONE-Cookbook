@echo off
rem Run Proof Gallery live smokes (all implementations or one --repo).
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\run_live_smoke.cmd [--repo smolagents] [--live] [--crew]
uv run --no-project --quiet python "%~dp0gallery.py" live-smoke %*
exit /b %ERRORLEVEL%
