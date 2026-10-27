[Setup]
AppId={{9B7F1D8C-4E23-4A59-86BC-193D8E24C781}
AppName=Campus Wi-Fi Auto-Login
AppVersion=1.0.0
AppPublisher=Campus Wi-Fi Project
DefaultDirName={localappdata}\Programs\CampusWifiLogin
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=CampusWifiLogin-Setup
SetupIconFile=app_icon.ico
LicenseFile=LICENSE.txt
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\app_icon.ico

VersionInfoCompany=Campus Wi-Fi Project
VersionInfoDescription=Campus Wi-Fi Auto-Login Setup
VersionInfoVersion=1.0.0.0
VersionInfoProductName=Campus Wi-Fi Auto-Login

[Files]
Source: "CampusWifiLogin.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\Campus Wi-Fi Settings"; Filename: "{app}\CampusWifiLogin.exe"; Parameters: "--config"; IconFilename: "{app}\app_icon.ico"
Name: "{userdesktop}\Campus Wi-Fi Settings"; Filename: "{app}\CampusWifiLogin.exe"; Parameters: "--config"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\CampusWifiLogin.exe"; Parameters: "--install"; Flags: runhidden
Filename: "{app}\CampusWifiLogin.exe"; Parameters: "--config"; Description: "Configure Wi-Fi credentials now"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\CampusWifiLogin.exe"; Parameters: "--uninstall"; Flags: runhidden
