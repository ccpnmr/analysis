@echo off
setlocal
set CCPNMR_TOP_DIR=%~dp0\..
call "%~dp0\paths"

"%ANACONDA3%"\python %*
endlocal

PAUSE
