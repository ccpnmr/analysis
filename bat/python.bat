@echo off
setlocal
pushd..
set CCPNMR_TOP_DIR=%CD%
popd
call "paths"

"%ANACONDA3%"\python %*
endlocal
