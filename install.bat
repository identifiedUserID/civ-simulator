@echo off
title Installing Python Civ Sim Prototype

echo ===================================
echo Python Civ Sim Prototype Installer
echo ===================================
echo.
echo This script will install required Python packages and create a Desktop shortcut.
echo Make sure you have Python 3 and Pip installed and added to your system PATH.
echo.
pause
echo.

:: Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

:: Navigate to the script directory (handles spaces in path)
cd /d "%SCRIPT_DIR%"

echo Installing required Python packages using pip...
echo This might take a moment.
echo.

:: Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found in the script directory!
    pause
    exit /b 1
)

:: Install requirements
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ---------------------------------------------------------------
    echo ERROR: Failed to install Python packages.
    echo Please ensure Python and Pip are installed correctly and run:
    echo pip install -r requirements.txt
    echo manually in this directory.
    echo ---------------------------------------------------------------
    pause
    exit /b 1
)

echo.
echo Packages installed successfully.
echo.
echo Creating Desktop Shortcut...

:: --- Create VBScript to make shortcut ---
set VBS_FILE="%TEMP%\temp_shortcut_%RANDOM%.vbs"
(
    echo Set oWS = WScript.CreateObject("WScript.Shell")
    echo sLinkFile = oWS.ExpandEnvironmentStrings("%%USERPROFILE%%\Desktop\Civ Sim Prototype.lnk")
    echo Set oLink = oWS.CreateShortcut(sLinkFile)
    echo oLink.TargetPath = "pythonw.exe"
    echo oLink.Arguments = """%SCRIPT_DIR%main.py"""
    echo oLink.Description = "Run the Python Civ Sim Prototype"
    echo oLink.IconLocation = "pythonw.exe, 0"
    echo oLink.WorkingDirectory = """%SCRIPT_DIR%"""
    echo oLink.WindowStyle = 1
    echo oLink.Save
    echo Set oLink = Nothing
    echo Set oWS = Nothing
) > %VBS_FILE%

:: Run the VBScript using cscript
cscript //nologo %VBS_FILE%

:: Check if shortcut creation seemed okay (basic check)
if not exist "%USERPROFILE%\Desktop\Civ Sim Prototype.lnk" (
   echo WARNING: Could not automatically verify shortcut creation.
   echo Please check your Desktop. If the shortcut is missing, you may need
   echo to create it manually. Target: pythonw.exe, Arguments: "%SCRIPT_DIR%main.py"
) else (
   echo Shortcut created on your Desktop!
)

:: Clean up the temporary VBScript file
if exist %VBS_FILE% del %VBS_FILE%

echo.
echo ===================================
echo Installation Complete!
echo ===================================
echo.
echo You can now run the game using the "Civ Sim Prototype" shortcut on your Desktop.
echo Or, you can run 'run_game.bat' from this folder.
echo.
pause
exit /b 0