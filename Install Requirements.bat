@echo off
setlocal

set "BASE_DIR=%~dp0"
set "REQ_FILE=%BASE_DIR%requirements.txt"

echo PDF Extraction Tool v1 - Install Requirements
echo =============================================
echo.

call :find_python
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo.
    echo Please install Python 3 from python.org, then run this file again.
    echo During installation, choose "Add python.exe to PATH" if available.
    echo.
    pause
    exit /b 1
)

echo Using Python:
%PYTHON_CMD% --version
echo.

%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r "%REQ_FILE%"

if errorlevel 1 (
    echo.
    echo ERROR: Requirements installation failed.
    echo Check the messages above, then try again.
    echo.
    pause
    exit /b 1
)

echo.
echo Installation complete.
echo You can now run Run PDF Extraction.bat.
echo.
pause
exit /b 0

:find_python
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

exit /b 1
