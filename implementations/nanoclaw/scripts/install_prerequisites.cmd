@echo off
rem Print NanoClaw + EXAONE prerequisite checklist (no package installs).
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\nanoclaw\scripts\install_prerequisites.cmd
uv run --no-project --quiet python "%~dp0..\..\gallery.py" nanoclaw-prereqs %*
exit /b %ERRORLEVEL%
