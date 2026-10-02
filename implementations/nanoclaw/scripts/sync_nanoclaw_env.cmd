@echo off
rem Render implementations/nanoclaw/.env EXAONE_* as OpenCode vars under _out/ only (DRY_RUN=1 prints only).
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\nanoclaw\scripts\sync_nanoclaw_env.cmd
uv run --no-project --quiet python "%~dp0..\..\gallery.py" nanoclaw-sync-env %*
exit /b %ERRORLEVEL%
