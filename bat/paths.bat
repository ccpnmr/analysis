@echo off
REM pushd..
REM set CCPNMR_TOP_DIR=%CD%
REM popd

set ANACONDA3=%CCPNMR_TOP_DIR%\miniconda
set PYTHONPATH=%CCPNMR_TOP_DIR%\src\python;%CCPNMR_TOP_DIR%\src\c
REM set FONTCONFIG_FILE=%ANACONDA3%\etc\fonts\fonts.conf
REM set FONTCONFIG_PATH=%ANACONDA3%\etc\fonts
set QT_PLUGIN_PATH=%QT_PLUGIN_PATH%;%ANACONDA3%\plugins
set QT_LOGGING_RULES="*.debug=false;qt.qpa.*=false"
set PATH=%ANACONDA3%\lib\site-packages\numpy\.libs;%ANACONDA3%;%ANACONDA3%\Library\mingw-w64\bin;%ANACONDA3%\Library\usr\bin;%ANACONDA3%\Library\bin;%ANACONDA3%\Scripts;%ANACONDA3%\bin;%CCPNMR_TOP_DIR%\bin;%PATH%
set LD_LIBRARY_PATH=%ANACONDA3%\lib
