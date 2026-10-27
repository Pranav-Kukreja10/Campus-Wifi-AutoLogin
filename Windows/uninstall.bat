@echo off
setlocal

set "TARGET_DIR=%LOCALAPPDATA%\Programs\CampusWifiLogin"

if exist "%TARGET_DIR%\CampusWifiLogin.exe" (
    "%TARGET_DIR%\CampusWifiLogin.exe" --uninstall
) else if exist "%TARGET_DIR%\captive_portal_login.py" (
    python "%TARGET_DIR%\captive_portal_login.py" --uninstall
) else (
    schtasks /Delete /TN "CampusWifiLogin" /F 2>nul
)

powershell -NoProfile -Command "Remove-Item \"$([Environment]::GetFolderPath('Programs'))\Campus Wi-Fi Settings.lnk\" -ErrorAction SilentlyContinue"
rmdir /S /Q "%TARGET_DIR%" 2>nul

echo Uninstallation finished successfully.
