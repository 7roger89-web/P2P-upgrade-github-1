@echo off
setlocal EnableExtensions

rem ============================================================
rem P2P_UPDATE_ALL_PROJECTS.bat
rem
rem One-click Windows wrapper around the canonical P2P batch sync:
rem   scripts\p2p_sync_managed_projects.py
rem
rem What it does:
rem - Regenerates stale .p2p\portable\P2P-OPERATIONS-NOTEBOOK.md
rem - Refreshes the managed P2P block in AGENTS.md
rem - Uses the current P2P checkout as the package/canonical source
rem - Skips current projects
rem - Refuses to overwrite dirty/conflicting AGENTS.md or portable law files
rem - Does NOT commit, push, merge, deploy, change secrets, or install runtime
rem
rem Usage:
rem   Double-click:
rem     Scans the drive containing this P2P checkout, plus <drive>\AI if present.
rem
rem   Or pass/drag one or more project/workspace folders:
rem     P2P_UPDATE_ALL_PROJECTS.bat "D:\Projects" "E:\Work"
rem     P2P_UPDATE_ALL_PROJECTS.bat "D:\Logistics_App_Copy"
rem ============================================================

set "P2P_ROOT=%~dp0"
if "%P2P_ROOT:~-1%"=="\" set "P2P_ROOT=%P2P_ROOT:~0,-1%"
set "SYNC_SCRIPT=%P2P_ROOT%\scripts\p2p_sync_managed_projects.py"

echo.
echo ============================================================
echo P2P - UPDATE ALL MANAGED PROJECTS
echo SOURCE: %P2P_ROOT%
echo ============================================================
echo.

if not exist "%SYNC_SCRIPT%" (
    echo [ERROR] Missing canonical sync script:
    echo         %SYNC_SCRIPT%
    echo.
    echo Run this batch from the root of the P2P source checkout.
    exit /b 2
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto :python_ready
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :python_ready
)

echo [ERROR] Python was not found in PATH.
echo Install/use the same Python environment already used by P2P.
exit /b 2

:python_ready
%PY_CMD% -c "import sys; print('Python:', sys.executable)" || exit /b 2

set "ANY_TARGET=0"

if "%~1"=="" (
    rem Beginner-friendly default for the Owner's normal Windows layout:
    rem scan the drive holding P2P, then its AI workspace when present.
    set "DEFAULT_DRIVE=%~d0\"
    call :SYNC_TARGET "%DEFAULT_DRIVE%"
    if exist "%~d0\AI\" call :SYNC_TARGET "%~d0\AI"
    goto :done
)

:arg_loop
if "%~1"=="" goto :done
call :SYNC_TARGET "%~1"
shift
goto :arg_loop

:SYNC_TARGET
set "TARGET=%~1"
if not exist "%TARGET%\" (
    echo [SKIP] Not found: %TARGET%
    echo.
    goto :eof
)

set "ANY_TARGET=1"
echo ------------------------------------------------------------
echo TARGET: %TARGET%

rem If TARGET itself is already a P2P-managed project, sync it directly.
if exist "%TARGET%\.p2p\portable\" goto :sync_project
if exist "%TARGET%\.p2p\system\" goto :sync_project

if exist "%TARGET%\AGENTS.md" (
    findstr /C:"<!-- BEGIN P2P CODEX -->" "%TARGET%\AGENTS.md" >nul 2>&1
    if not errorlevel 1 goto :sync_project
    findstr /C:"<!-- BEGIN P2P PORTABLE LAW -->" "%TARGET%\AGENTS.md" >nul 2>&1
    if not errorlevel 1 goto :sync_project
)

rem Otherwise treat TARGET as a workspace containing P2P-managed repos.
echo MODE: WORKSPACE
%PY_CMD% "%SYNC_SCRIPT%" --workspace "%TARGET%" --package-root "%P2P_ROOT%" --write
echo.
goto :eof

:sync_project
echo MODE: PROJECT
%PY_CMD% "%SYNC_SCRIPT%" --project "%TARGET%" --package-root "%P2P_ROOT%" --write
echo.
goto :eof

:done
echo ============================================================
if "%ANY_TARGET%"=="0" (
    echo No valid target was found.
    exit /b 2
)

echo Finished.
echo Review each summary line:
echo   CURRENT / UPDATED = OK
echo   BLOCKED           = intentionally skipped; inspect the reason
echo.
echo This batch does NOT git commit/push any project.
echo ============================================================
echo.

if "%~1"=="" pause
exit /b 0
