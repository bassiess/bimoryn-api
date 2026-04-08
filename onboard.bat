@echo off
:: BIMoryn Pilot Onboarding
:: Installs dependencies and validates the demo model.
:: Requirements: Python 3.11+

echo.
echo ============================================
echo   BIMoryn -- BIM Validation Engine
echo   Pilot Onboarding
echo ============================================
echo.

:: Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found.
    echo Please install Python 3.11 or later from https://www.python.org/downloads/
    echo Make sure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYVER=%%v
echo Python %PYVER% found.
echo.

:: Install BIMoryn
echo Installing BIMoryn...
python -m pip install -e . --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Installation failed. Check pip output above.
    pause
    exit /b 1
)
echo Done.
echo.

:: Run demo validation
echo Running validation on samples\demo.ifc...
echo --------------------------------------------
bimoryn validate samples\demo.ifc
echo --------------------------------------------
echo.

:: Save JSON report
echo Saving JSON report to demo-report.json...
bimoryn validate samples\demo.ifc --output demo-report.json --quiet
echo Report saved: demo-report.json
echo.
echo ============================================
echo   Setup complete!
echo.
echo   To validate your own model:
echo     bimoryn validate path\to\your-model.ifc
echo.
echo   To save a BCF file for Revit / Solibri:
echo     bimoryn validate model.ifc --output issues.bcfzip --format bcf
echo.
echo   To list all rules:
echo     bimoryn rules list
echo ============================================
echo.
pause
