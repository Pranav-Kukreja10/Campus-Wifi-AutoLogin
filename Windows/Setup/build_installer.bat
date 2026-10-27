@echo off
setlocal
echo ========================================================
echo Building Campus Wi-Fi Auto-Login Inno Setup Installer
echo ========================================================

:: Ensure CampusWifiLogin.exe is present in Setup directory
if not exist "CampusWifiLogin.exe" (
    if exist "..\CampusWifiLogin.exe" (
        echo Copying ..\CampusWifiLogin.exe into Setup directory...
        copy /Y "..\CampusWifiLogin.exe" "CampusWifiLogin.exe" >nul
    ) else (
        echo [ERROR] CampusWifiLogin.exe was not found.
        echo Please compile it first using Windows\build_nuitka.bat.
        if not defined CI pause
        exit /b 1
    )
)

:: Sync LICENSE.txt
if exist "..\..\LICENSE.txt" (
    copy /Y "..\..\LICENSE.txt" "LICENSE.txt" >nul
)

:: Locate Inno Setup Compiler (ISCC.exe)
set "ISCC_PATH="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if defined ISCC_PATH (
    echo Compiling with %ISCC_PATH%...
    "%ISCC_PATH%" setup.iss
    if %ERRORLEVEL% equ 0 (
        echo.
        echo [SUCCESS] Installer generated: CampusWifiLogin-Setup.exe
    ) else (
        echo.
        echo [ERROR] Inno Setup compilation failed.
    )
) else (
    echo [INFO] Inno Setup CLI (ISCC.exe) was not found in standard paths.
    echo Please install Inno Setup 6 (https://jrsoftware.org/isdl.php)
    echo or open 'setup.iss' directly in Inno Setup Compiler and press Ctrl+F9.
)

if not defined CI pause

