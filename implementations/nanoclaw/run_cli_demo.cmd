@echo off
rem NanoClaw + EXAONE demo helper (does NOT modify submodules/nanoclaw).
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\nanoclaw\run_cli_demo.cmd [--live]
uv run --no-project --quiet python "%~dp0..\gallery.py" demo nanoclaw %*
exit /b %ERRORLEVEL%
