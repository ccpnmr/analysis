@echo off
setlocal
pushd..
set CCPNMR_TOP_DIR=%CD%
popd
call "%CCPNMR_TOP_DIR%\bin\paths"

set ENTRYMODULE="%CCPNMR_TOP_DIR%"\src\python\ccpn\AnalysisAssign.py
"%ANACONDA3%"\python -i -O -W ignore::DeprecationWarning "%ENTRYMODULE%" %*
endlocal
