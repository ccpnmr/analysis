@echo off
setlocal
pushd..
set CCPNMR_TOP_DIR=%CD%
popd
call "paths"

set ENTRYMODULE="%CCPNMR_TOP_DIR%"\src\python\ccpn\util\convertPaths.py

set ROOT="%HOME%\release\ccpnmr3.0.0\miniconda"
set PATHFROM="%ANACONDA3%"
set PATHTO="%HOME%\release\ccpnmr3.0.0\miniconda"

"%ANACONDA3%"\python -i -O -W ignore "%ENTRYMODULE%" "%ROOT%" "%PATHFROM%" "%PATHTO%"
endlocal
