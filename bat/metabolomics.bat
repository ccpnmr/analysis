@echo off
setlocal
pushd..
set CCPNMR_TOP_DIR=%CD%
popd
call "paths"

set ENTRYMODULE="%CCPNMR_TOP_DIR%"\src\python\ccpn\AnalysisMetabolomics
"%ANACONDA3%"\python -i -O -W ignore "%ENTRYMODULE%" %*
endlocal
