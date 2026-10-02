@echo off
rem Non-interactive CrewAI + EXAONE demo orchestrator.
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\crewai\run_cli_demo.cmd [--live] [--crew]
uv run --no-project --quiet python "%~dp0..\gallery.py" demo crewai %*
exit /b %ERRORLEVEL%
