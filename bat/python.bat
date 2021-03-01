@echo off
setlocal
set CCPNMR_TOP_DIR=%~dp0\..
call "%~dp0\paths"

"%CONDA%"\python %*
endlocal

PAUSE
