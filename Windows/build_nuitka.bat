@echo off
pip install nuitka requests keyring
python -m nuitka --onefile --windows-console-mode=disable --assume-yes-for-downloads --enable-plugin=tk-inter --include-package=keyring --include-package=requests --windows-icon-from-ico=app_icon.ico --include-data-file=app_icon.ico=app_icon.ico --include-data-file=app_icon.png=app_icon.png --output-filename=CampusWifiLogin.exe captive_portal_login.py
if %ERRORLEVEL% neq 0 (
    if not defined CI pause
    exit /b %ERRORLEVEL%
)
if not defined CI pause
