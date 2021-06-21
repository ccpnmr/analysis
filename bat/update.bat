@echo off
setlocal

set MODULE=src\python\ccpn\util\Update.py

set CCPNMR_TOP_DIR=%~dpnx0
set /a "_count=0"
:_countLoop
    call :isLink _SYM "%CCPNMR_TOP_DIR%"
    call :fileName _PATH "%CCPNMR_TOP_DIR%"
    set "_FOUND="
    FOR /F "tokens=2 delims=[]" %%G in ('"dir  /AL "%CCPNMR_TOP_DIR%"\.. 2^>nul | find "%_PATH%""') do set "_FOUND=%%G"
    if defined _SYM if defined _FOUND call :AbsPath CCPNMR_TOP_DIR "%_FOUND%"
    call :AbsPath CCPNMR_TOP_DIR "%CCPNMR_TOP_DIR%"\..

    set /a "_count=_count+1"
    if %_count% lss 2 goto _countLoop

call "%CCPNMR_TOP_DIR%\bat\paths"

set ENTRY_MODULE=%CCPNMR_TOP_DIR%\%MODULE%
"%CONDA%"\python -i -O -W ignore "%ENTRY_MODULE%" %*
endlocal

PAUSE
exit /b

:AbsPath
    REM return absolute name of input path
    REM :param %1: Name of output variable
    REM :param %2: input path
    REM :return: absolute path
    set %1=%~f2
    exit /b

:fileName
    REM return absolute name of input path
    REM :param %1: Name of output variable
    REM :param %2: input path
    REM :return: absolute path
    set %1=%~nx2
    exit /b

:isLink
    REM return if path object is a symlink
    REM :param %1: Name of output variable
    REM :param %2: input path
    REM :return: true (variable defined) if symlink
    set "%1="
    for %%i in ("%~f2") do set attribute=%%~ai
    set attribute=%attribute:~8,1%
    if "%attribute%" == "l" set "%1=true"
    exit /b
