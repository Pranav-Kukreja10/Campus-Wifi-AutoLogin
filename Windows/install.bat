@echo off
setlocal

set "TARGET_DIR=%LOCALAPPDATA%\Programs\CampusWifiLogin"
mkdir "%TARGET_DIR%" 2>nul

if exist "CampusWifiLogin.exe" (
    copy /Y "CampusWifiLogin.exe" "%TARGET_DIR%\CampusWifiLogin.exe" >nul
    "%TARGET_DIR%\CampusWifiLogin.exe" --install
    powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\"$([Environment]::GetFolderPath('Programs'))\Campus Wi-Fi Settings.lnk\"); $s.TargetPath = \"$env:LOCALAPPDATA\Programs\CampusWifiLogin\CampusWifiLogin.exe\"; $s.Arguments = \"--config\"; $s.Save()"
    start "" "%TARGET_DIR%\CampusWifiLogin.exe" --config
) else if exist "dist\CampusWifiLogin.exe" (
    copy /Y "dist\CampusWifiLogin.exe" "%TARGET_DIR%\CampusWifiLogin.exe" >nul
    "%TARGET_DIR%\CampusWifiLogin.exe" --install
    powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\"$([Environment]::GetFolderPath('Programs'))\Campus Wi-Fi Settings.lnk\"); $s.TargetPath = \"$env:LOCALAPPDATA\Programs\CampusWifiLogin\CampusWifiLogin.exe\"; $s.Arguments = \"--config\"; $s.Save()"
    start "" "%TARGET_DIR%\CampusWifiLogin.exe" --config
) else (
    copy /Y "config_manager.py" "%TARGET_DIR%\" >nul
    copy /Y "engine.py" "%TARGET_DIR%\" >nul
    copy /Y "gui.py" "%TARGET_DIR%\" >nul
    copy /Y "task_manager.py" "%TARGET_DIR%\" >nul
    copy /Y "captive_portal_login.py" "%TARGET_DIR%\" >nul
    copy /Y "main.py" "%TARGET_DIR%\" >nul
    python "%TARGET_DIR%\captive_portal_login.py" --install
    powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\"$([Environment]::GetFolderPath('Programs'))\Campus Wi-Fi Settings.lnk\"); $s.TargetPath = (Get-Command pythonw.exe).Source; $s.Arguments = \"`\"$env:LOCALAPPDATA\Programs\CampusWifiLogin\captive_portal_login.py`\" --config\"; $s.WorkingDirectory = \"$env:LOCALAPPDATA\Programs\CampusWifiLogin\"; $s.Save()"
    start "" pythonw "%TARGET_DIR%\captive_portal_login.py" --config
)

echo Installation finished successfully.
