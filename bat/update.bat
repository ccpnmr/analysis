@echo off
setlocal
set CCPNMR_TOP_DIR=%~dp0\..
call "%~dp0\paths"

set ENTRYMODULE=%CCPNMR_TOP_DIR%\src\python\ccpn\util\Update.py
"%ANACONDA3%"\python -i -O -W ignore "%ENTRYMODULE%" %*
endlocal
