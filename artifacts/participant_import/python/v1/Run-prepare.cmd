@echo off
setlocal DisableDelayedExpansion
if "%~1"=="" (
  echo Drag the original Excel workbook onto this file.
  echo Or run: Run-prepare.cmd "C:\path\original.xlsx" 206
  echo The optional second number skips that many data rows. Default is 0.
  pause
  exit /b 1
)
set "TANDEM_PYTHON=C:\projects\small_projects\tandem-language-culture-app\.venv\Scripts\python.exe"
set "TANDEM_INPUT=--workbook"
if /I "%~x1"==".csv" set "TANDEM_INPUT=--prepared-csv"
set "TANDEM_SKIP=0"
if not "%~2"=="" set "TANDEM_SKIP=%~2"
if exist "%TANDEM_PYTHON%" (
  "%TANDEM_PYTHON%" "%~dp0import_participants_once.py" %TANDEM_INPUT% "%~f1" --skip-rows "%TANDEM_SKIP%"
) else (
  py -3 "%~dp0import_participants_once.py" %TANDEM_INPUT% "%~f1" --skip-rows "%TANDEM_SKIP%"
)
if errorlevel 1 (
  echo Preparation did not complete. Check the message above.
) else (
  echo Done. Open the new Tandem-import folder beside your input file.
  echo No participant records were changed. Review participants.csv and manual-review.csv.
)
pause
