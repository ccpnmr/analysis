@echo off
set CONDA=%PROJECT_DEFAULT%\miniconda
set PYTHONPATH=%PROJECT_DEFAULT%\src\python;%PROJECT_DEFAULT%\src\c
set QT_PLUGIN_PATH=%CONDA%\Library\plugins
set PATH=%CONDA%\lib\site-packages\numpy\.libs;^
%CONDA%;^
%CONDA%\Library\mingw-w64\bin;^
%CONDA%\Library\usr\bin;^
%CONDA%\Library\bin;^
%CONDA%\Scripts;^
%CONDA%\bin;^
%PROJECT_DEFAULT%\bin;%PATH%
set LD_LIBRARY_PATH=%CONDA%\lib
set QT_LOGGING_RULES=*=false
