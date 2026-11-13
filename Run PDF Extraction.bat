@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "BASE_DIR=%~dp0"
set "INPUT_DIR=%BASE_DIR%input"
set "SCRIPT_PATH=%BASE_DIR%src\extract_pdf_fields.py"
set "OUTPUT_BASE=%BASE_DIR%output"

call :find_python
if errorlevel 1 (
  echo ERROR: Python 3 not found. Install Python, then run Install Requirements.bat.
  pause
  exit /b 1
)
if not exist "%SCRIPT_PATH%" (
  echo ERROR: Extraction script is missing.
  pause
  exit /b 1
)
if not exist "%INPUT_DIR%" mkdir "%INPUT_DIR%"
if not exist "%OUTPUT_BASE%" mkdir "%OUTPUT_BASE%"
%PYTHON_CMD% -c "import pdfplumber, openpyxl" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Dependencies missing. Run Install Requirements.bat.
  pause
  exit /b 1
)
dir /b "%INPUT_DIR%\*.pdf" >nul 2>nul
if errorlevel 1 (
  echo No PDF files found under input.
  pause
  exit /b 0
)

rem Never delete prior outputs. Use a timestamp plus collision counter.
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "RUN_STAMP=%%I"
if not defined RUN_STAMP set "RUN_STAMP=%RANDOM%_%RANDOM%"
set "RUN_DIR=%OUTPUT_BASE%\run_%RUN_STAMP%"
set /a RUN_COUNTER=2
:choose_run_directory
if exist "!RUN_DIR!" (
  set "RUN_DIR=%OUTPUT_BASE%\run_%RUN_STAMP%_!RUN_COUNTER!"
  set /a RUN_COUNTER+=1
  goto choose_run_directory
)
mkdir "!RUN_DIR!" || (
  echo ERROR: Could not create output run directory.
  pause
  exit /b 1
)

%PYTHON_CMD% "%SCRIPT_PATH%" --input "%INPUT_DIR%" --output extraction_report.xlsx --output-root "!RUN_DIR!" --scan-policy manual_review
if errorlevel 1 (
  echo ERROR: Extraction failed. Previously created outputs were preserved.
  pause
  exit /b 1
)
echo.
echo Done. Results are in: !RUN_DIR!
pause
exit /b 0

:find_python
where py >nul 2>nul
if not errorlevel 1 (set "PYTHON_CMD=py -3" & exit /b 0)
where python >nul 2>nul
if not errorlevel 1 (set "PYTHON_CMD=python" & exit /b 0)
exit /b 1
