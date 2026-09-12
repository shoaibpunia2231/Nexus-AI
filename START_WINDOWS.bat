@echo off
setlocal
title Nexus AI - Launcher
color 0A
cls

echo.
echo  =====================================================
echo    Nexus AI - Dengue Risk Screening System
echo  =====================================================
echo.
echo  Starting setup... window will stay open.
echo.

REM ROOT ends with backslash
set ROOT=%~dp0
set ML=%ROOT%ml
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend
set REQFILE=%ROOT%requirements.txt
set MODELPKL=%ROOT%ml\models\model.pkl

REM Add common Node.js paths
set PATH=%PATH%;C:\Program Files\nodejs
set PATH=%PATH%;%LOCALAPPDATA%\Programs\nodejs
set PATH=%PATH%;%APPDATA%\npm

echo [1/6] Checking Python...
python --version >nul 2>nul
if not errorlevel 1 goto PYTHON_OK
py --version >nul 2>nul
if not errorlevel 1 goto PY_OK
echo  ERROR: Python not found. Get it from https://www.python.org/downloads/
echo  During install TICK: Add Python to PATH
goto FAIL
:PY_OK
set PYTHON=py
goto PYTHON_DONE
:PYTHON_OK
set PYTHON=python
:PYTHON_DONE
%PYTHON% --version
echo  Python: OK
echo.

echo [2/6] Checking Node.js...
node --version >nul 2>nul
if not errorlevel 1 goto NODE_OK
echo  ERROR: node not found. Restart your computer then try again.
goto FAIL
:NODE_OK
node --version
echo  Node.js: OK
echo.

echo [3/6] Installing Python packages...
%PYTHON% -m pip install -r "%REQFILE%" -q --disable-pip-version-check
if errorlevel 1 (
  echo  ERROR: pip install failed.
  goto FAIL
)
echo  Python packages: OK
echo.

echo [4/6] Checking trained model...
if exist "%MODELPKL%" goto MODEL_EXISTS
echo  Training model ~30 seconds...
cd /d "%ML%"
%PYTHON% train_model.py
if errorlevel 1 ( echo  ERROR: Training failed. & goto FAIL )
cd /d "%ROOT%"
echo  Model: OK
goto MODEL_DONE
:MODEL_EXISTS
echo  model.pkl found - skipping.
:MODEL_DONE
echo.

echo [5/6] Installing frontend packages...
cd /d "%FRONTEND%"
call npm install
if errorlevel 1 ( echo  ERROR: npm install failed. & goto FAIL )
cd /d "%ROOT%"
echo  Frontend: OK
echo.

echo [6/6] Launching...

REM Write tiny helper bat files so start has no nested-quote issues
(
  echo @echo off
  echo cd /d "%BACKEND%"
  echo %PYTHON% -m uvicorn main:app --reload --port 8000
) > "%ROOT%_backend_run.bat"

(
  echo @echo off
  echo cd /d "%FRONTEND%"
  echo npm run dev
) > "%ROOT%_frontend_run.bat"

start "Nexus AI Backend"  cmd /k "%ROOT%_backend_run.bat"
timeout /t 5 /nobreak >nul
start "Nexus AI Frontend" cmd /k "%ROOT%_frontend_run.bat"
timeout /t 8 /nobreak >nul
start http://localhost:5173

echo.
echo  ====================================================
echo   App is running!
echo   Frontend : http://localhost:5173
echo   API Docs : http://localhost:8000/docs
echo   Keep the two terminal windows open.
echo   To stop  : close those two windows.
echo  ====================================================
echo.
pause
exit /b 0

:FAIL
echo.
echo  ====================================================
echo   Setup failed. Read the error above.
echo   Fix it then run START_WINDOWS.bat again.
echo  ====================================================
echo.
pause
exit /b 1
