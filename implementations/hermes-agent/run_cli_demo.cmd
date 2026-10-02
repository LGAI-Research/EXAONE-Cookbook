@echo off
rem Non-interactive smoke: check, render, ping, doctor.
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\hermes-agent\run_cli_demo.cmd [--live]
uv run --no-project --quiet python "%~dp0..\gallery.py" demo hermes-agent %*
exit /b %ERRORLEVEL%
