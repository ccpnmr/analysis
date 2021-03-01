@echo off
set CONDA=%CCPNMR_TOP_DIR%\miniconda
set PYTHONPATH=%CCPNMR_TOP_DIR%\src\python;%CCPNMR_TOP_DIR%\src\c
set QT_PLUGIN_PATH=%CONDA%\Library\plugins
set PATH=%CONDA%\lib\site-packages\numpy\.libs;^
%CONDA%;^
%CONDA%\Library\mingw-w64\bin;^
%CONDA%\Library\usr\bin;^
%CONDA%\Library\bin;^
%CONDA%\Scripts;^
%CONDA%\bin;^
%CCPNMR_TOP_DIR%\bin;%PATH%
set LD_LIBRARY_PATH=%CONDA%\lib
set QT_LOGGING_RULES=*=false
