@echo off
setlocal
set CCPNMR_TOP_DIR=%~dp0\..
call "%~dp0\paths"

set ENTRY_MODULE=%CCPNMR_TOP_DIR%\src\python\ccpn\util\convertPaths.py
set ROOT=%HOME%\%RELEASE%\%CCPNMR_PATH%\miniconda
set PATHFROM=%CONDA%
set PATHTO=%HOME%\%RELEASE%\%CCPNMR_PATH%\miniconda

"%CONDA%"\python -i -O -W ignore "%ENTRY_MODULE%" "%ROOT%" "%PATHFROM%" "%PATHTO%"
endlocal

PAUSE
