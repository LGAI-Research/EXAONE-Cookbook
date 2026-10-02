@echo off
rem Print OneCLI secret registration hints for EXAONE (does not call onecli).
rem Thin wrapper for PowerShell/cmd - logic lives in implementations\gallery.py.
rem Usage (cookbook root): implementations\nanoclaw\scripts\print_onecli_exaone.cmd
uv run --no-project --quiet python "%~dp0..\..\gallery.py" nanoclaw-onecli %*
exit /b %ERRORLEVEL%
