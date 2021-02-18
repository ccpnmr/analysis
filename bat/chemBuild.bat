@echo off
setlocal
set CCPNMR_TOP_DIR=%~dp0\..
call "%~dp0\paths"

rem redefine PYTHONPATH from default
set PYTHONPATH=%CCPNMR_TOP_DIR%\src\python\chemBuild;%PYTHONPATH%

set ENTRY_MODULE=%CCPNMR_TOP_DIR%\src\python\chemBuild\ccpnmr\chemBuild\ChemBuild.py
"%CONDA%"\python -i -O -W ignore "%ENTRY_MODULE%" %*
endlocal

PAUSE
