@echo off
setlocal
pushd..
set CCPNMR_TOP_DIR=%CD%
popd
call "paths"

set ENTRYMODULE="%CCPNMR_TOP_DIR%"\src\python\ccpn\util\nef\CompareNef.py
"%ANACONDA3%"\python -i -O -W ignore::DeprecationWarning "%ENTRYMODULE%" %*
endlocal
