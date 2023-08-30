@echo off
setlocal enabledelayedexpansion

set MODULE=src\python\ccpn\util\Update.py


set "autoUpdate=false"
set "args=%*"
set /a "n=0"

for %%a in (%args%) do (
    set /a "n+=1"
    set "arg=%%~a"

    if "!arg!"=="--auto-update" (
        set "autoUpdate=true"
        if !n! EQU 1 (
            set "args=!args:~0,-1!"
        ) else (
            set "args=!args:~0,-!n!!args:~!n!+1!"
        )
    )
)

echo Auto Update: %autoUpdate%
echo Remaining Args: %args%



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
"%CONDA%\python.exe" -i -O -W ignore "%ENTRY_MODULE%" %*
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
    REM :return: filename
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

REM ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@echo off
setlocal enabledelayedexpansion

REM Get the script file if symbolic
set "_path=%~dp0"

REM Initialize variables
set "autoUpdate="
set "args="

REM Check for --auto-update in the switches
for %%a in (%*) do (
    set "arg=%%~a"
    if "!arg!"=="--auto-update" (
        set "autoUpdate=true"
    ) else (
        set "args=!args! "%%~a""
    )
)

REM Iterate through the symbolic links if needed
for /l %%i in (1,1,3) do (
    if exist "!_path!\nul" (
        pushd "!_path!" && set "_path=!cd!"
    )
    set "_pathlink="
    for /f "usebackq delims=" %%j in (`for %%k in ("!_path!") do echo %%~fk`) do set "_pathlink=%%j"
    if "!_pathlink!"=="" set "_pathlink=!_path!"
    for /f "usebackq delims=" %%j in (`dir /b /ad "!_pathlink!"`) do set "_path=!_pathlink!"
)

REM Set CCPNMR_TOP_DIR
set "CCPNMR_TOP_DIR=!_pathlink!"
set "CCPN_PYTHON=\python\python.exe"

REM Update if the switch is found
if defined autoUpdate (
    call "!_path!\update.bat" %args%
    set "errlevel=!errorlevel!"
    if !errlevel! GEQ 32 (
        echo "--> there was an issue auto-updating: !errlevel!"
    )
)

REM Run analysis
set "ANALYSIS=!CCPNMR_TOP_DIR!\src\python\ccpn\AnalysisAssign"
"%CCPNMR_TOP_DIR%%CCPN_PYTHON%" -W ignore "%ANALYSIS%" %args%

endlocal
exit /b
