@echo off
setlocal

echo Setting up Public Health Intelligence Platform for Windows...
echo.
echo ---
echo [STEP 0/5] Cleaning up previous installations and caches...
echo ---

echo Clearing npm cache...
npm cache clean --force

echo Removing old frontend dependencies...
if exist "frontend\node_modules" (
    rmdir /s /q "frontend\node_modules"
)
if exist "frontend\package-lock.json" (
    del "frontend\package-lock.json"
)

echo Removing old backend environment...
if exist "backend\venv" (
    rmdir /s /q "backend\venv"
)

echo Cleanup complete.
echo.

echo ---
echo [STEP 1/5] Checking Environment and Prerequisites...
echo ---

REM --- Check for active Conda environment ---
IF DEFINED CONDA_PREFIX (
    echo.
    echo [CRITICAL ERROR] The script has detected that it is running inside a Conda environment.
    echo Your Conda environment is located at: %CONDA_PREFIX%
    echo.
    echo This will conflict with the script's own virtual environment.
    echo.
    echo Please take the following steps:
    echo 1. Close this window.
    echo 2. Open a NEW, standard Windows Command Prompt (cmd.exe).
    echo 3. Make sure you see "C:\>" and NOT "(base) C:\>" or "(phim) C:\>".
    echo 4. If you see "(base)", run "conda deactivate" until it disappears.
    echo 5. Navigate to the project folder and run this script again.
    echo.
    pause
    exit /b 1
)

REM --- Check for Python and Node.js ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system's PATH.
    echo Please install Python 3.11+ from python.org and ensure it's added to PATH.
    pause
    exit /b 1
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in your system's PATH.
    echo Please install Node.js 18+ from nodejs.org.
    pause
    exit /b 1
)

echo Prerequisites check passed!
echo.
echo ---
echo [STEP 2/5] Setting up Backend...
echo ---

cd backend

if not exist venv (
    echo Creating Python virtual environment in 'backend\venv\'...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create Python virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies. Please check the error messages above.
    pause
    exit /b 1
)

echo Backend setup complete!
cd ..
echo.

echo ---
echo [STEP 3/5] Setting up Frontend...
echo ---

cd frontend

echo Installing Node.js dependencies...
REM Use --legacy-peer-deps to resolve the known date-fns conflict automatically.
npm install --legacy-peer-deps
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies.
    echo Please check the npm error log mentioned in the output.
    pause
    exit /b 1
)

echo Frontend setup complete!
cd ..
echo.

echo ---
echo [STEP 4/5] Setup Complete!
echo ---
echo.
echo =================================================================
echo  Vanguard OS setup was successful.
echo =================================================================
echo.
echo To start the application, run the 'start-platform.bat' script.
echo It will open two new terminal windows for the backend and frontend.
echo.
pause
