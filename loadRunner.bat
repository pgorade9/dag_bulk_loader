@echo off
REM Navigate to the Python project directory
cd /d "C:\Users\pgorade\PycharmProjects\dag_bulk_loader"
if %errorlevel% neq 0 (
    echo Failed to navigate to Python project directory.
    exit /b
)

REM Activate the virtual environment (if applicable)
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate the virtual environment.
    exit /b
)

REM Run the Python script in a new process (daemon mode)
start "" python -m app.main
if %errorlevel% neq 0 (
    echo Failed to start the Python script in daemon mode.
    exit /b
)

REM Navigate to the Angular UI directory
cd /d "C:\Users\pgorade\VSCodeProjects\ui_dag_bulk_loader\app"
if %errorlevel% neq 0 (
    echo Failed to navigate to UI project directory.
    exit /b
)

REM Serve the Angular app
start "" ng serve --port 4201
if %errorlevel% neq 0 (
    echo Angular app failed to start.
    exit /b
)

@echo off
REM Launch Internet Explorer and open localhost:4201
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" http://localhost:4201

echo All tasks completed successfully!
