@echo off
rem Non-interactive smolagents + EXAONE demo orchestrator.
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\smolagents\run_cli_demo.cmd [--live]
uv run --no-project --quiet python "%~dp0..\gallery.py" demo smolagents %*
exit /b %ERRORLEVEL%
