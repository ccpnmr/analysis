@echo off
set ANACONDA3=%CCPNMR_TOP_DIR%\miniconda
set PYTHONPATH=%CCPNMR_TOP_DIR%\src\python;%CCPNMR_TOP_DIR%\src\c
set QT_PLUGIN_PATH=%QT_PLUGIN_PATH%;%ANACONDA3%\plugins
set PATH=%ANACONDA3%\lib\site-packages\numpy\.libs;%ANACONDA3%;%ANACONDA3%\Library\mingw-w64\bin;%ANACONDA3%\Library\usr\bin;%ANACONDA3%\Library\bin;%ANACONDA3%\Scripts;%ANACONDA3%\bin;%CCPNMR_TOP_DIR%\bin;%PATH%
set LD_LIBRARY_PATH=%ANACONDA3%\lib
set QT_LOGGING_RULES=*=false
