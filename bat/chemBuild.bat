@echo off
setlocal
set CCPNMR_TOP_DIR=%~dp0\..
call "%~dp0\paths"

rem redefine PYTHONPATH from default
set PYTHONPATH=%CCPNMR_TOP_DIR%\src\python\chemBuild;%PYTHONPATH%

set ENTRYMODULE=%CCPNMR_TOP_DIR%\src\python\chemBuild\ccpnmr\chemBuild\ChemBuild.py
"%ANACONDA3%"\python -i -O -W ignore "%ENTRYMODULE%" %*
endlocal

PAUSE
