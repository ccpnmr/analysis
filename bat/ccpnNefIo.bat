@echo off
setlocal
set CCPNMR_TOP_DIR=%~dp0\..
call "%~dp0\paths"

set ENTRY_MODULE=%CCPNMR_TOP_DIR%\src\python\ccpn\core\lib\CcpnNefIo.py
"%CONDA%"\python -i -O -W ignore "%ENTRY_MODULE%" %*
endlocal

PAUSE
