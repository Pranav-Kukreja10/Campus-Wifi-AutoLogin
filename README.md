# Campus Wi-Fi Auto-Login (Windows)

[![License](https://img.shields.io/badge/License-Non--Commercial-blue.svg)](LICENSE.txt)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6.svg)](README.md)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/Build-GitHub%20Actions-brightgreen.svg)](.github/workflows/build.yml)

An automated background authentication utility for university and campus captive Wi-Fi portals (such as Palo Alto Networks, Fortinet, SonicWall, and Aruba portals) on **Windows 10 and 11**.

Whenever your computer reconnects to campus Wi-Fi or wakes from sleep, **Campus Wi-Fi Auto-Login** detects the network state event and authenticates in the background in milliseconds—without opening browser tabs or requiring you to re-type credentials throughout the day.

---

> [!WARNING]
> ### ⚠️ Open-Source Disclaimer & Non-Liability Warning
> This software is an independent, open-source utility developed for **personal, educational, and convenience purposes only**.
>
> - **Zero Affiliation**: This project is not affiliated with, endorsed by, or sponsored by any university, educational institution, network administrator, or captive portal vendor (including Palo Alto Networks, Inc.).
> - **Compliance with Acceptable Use Policies (AUP)**: Users are solely and exclusively responsible for ensuring that running this utility adheres to their institution's Wi-Fi Terms of Service, Acceptable Use Policies, and network regulations.
> - **Absolute Disclaimer of Liability**: **The author(s) and maintainer(s) are NOT responsible for any type of violations, damages, network bans, MAC address blacklists, account suspensions, administrative penalties, or disciplinary actions arising from the installation, use, or misuse of this software.**
> - **Authorized Access Only**: You must only use your own legitimate, university-issued student or staff login credentials. This tool does not bypass authentication, crack passwords, or exploit vulnerabilities—it strictly automates the submission of credentials you have been legitimately authorized to use.

---

## 📑 Table of Contents
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Repository Structure](#-repository-structure)
- [How to Install & Setup](#-how-to-install--setup)
- [How to Use & Configure](#-how-to-use--configure)
- [Command-Line Usage (CLI)](#-command-line-usage-cli)
- [How to Completely Delete / Uninstall](#-how-to-completely-delete--uninstall)
- [How to Distribute Setup (For Maintainers)](#-how-to-distribute-setup-for-maintainers)
- [Building from Source](#-building-from-source)
- [Security & Credential Storage](#-security--credential-storage)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## ✨ Features

- ⚡ **Zero-Battery, Event-Driven**: Does **not** run a heavy polling loop in the background. It hooks directly into native Windows Task Scheduler event triggers (`EventID 10000` / `EventID 8001` on Wi-Fi connection).
- 🔐 **Secure Credential Protection**: Passwords are never stored in plaintext configuration files. They are encrypted and stored in your operating system's native hardware-backed vault (**Windows Credential Manager**) via Python `keyring`.
- 🖥️ **Modern Desktop GUI**: Includes an intuitive Tkinter dark-themed interface to configure your credentials, target Wi-Fi SSIDs, and portal addresses with one click.
- 🔒 **Process Lock Concurrency Control**: Uses native Windows file locking (`msvcrt`) to prevent duplicate login submissions if multiple network interfaces cycle simultaneously.
- 🎯 **Target SSID Whitelisting**: Automatically identifies your active Wi-Fi network and only attempts authentication when connected to authorized campus SSIDs (or all networks if left unrestricted).
- 🧹 **One-Click Total Wipe**: Offers clean uninstallation that purges all scheduled tasks, desktop shortcuts, configurations, and stored credentials with zero leftover registry clutter.

---

## ⚙️ How It Works

```
                       +-----------------------------+
                       | Wi-Fi Connects / Reconnects |
                       +--------------+--------------+
                                      |
                                      v
                       +-----------------------------+
                       |   Windows Task Scheduler    |
                       |  (EventID 10000 / 8001)     |
                       +--------------+--------------+
                                      |
                                      v
                        +---------------------------+
                        | CampusWifiLogin.exe       |
                        +-------------+-------------+
                                      |
                       [Check SSID in Whitelist?]
                                      |
                     +----------------+----------------+
                     | Yes                             | No
                     v                                 v
          [Probe Internet Status]                  [Exit cleanly]
                     |
       +-------------+-------------+
       | Online                    | Captive Portal Detected
       v                           v
  [Exit silently]         [Fetch Credentials from Keyring]
                                   |
                          [Submit Portal Form]
                                   |
                       +-----------+-----------+
                       | Success               | Failed
                       v                       v
               [Connected to Net]      [Prompt Re-Auth GUI]
```

---

## 📁 Repository Structure

```text
CampusLogin/
├── .github/
│   └── workflows/
│       └── build.yml             # GitHub Actions CI/CD (Windows compile & auto-release)
├── Windows/
│   ├── app_icon.ico              # Windows application icon
│   ├── app_icon.png              # High-resolution PNG icon
│   ├── build_nuitka.bat          # Compiles Python into standalone Windows .exe
│   ├── captive_portal_login.py   # Main CLI entry point & background controller
│   ├── config_manager.py         # JSON settings & Windows Credential Manager handler
│   ├── engine.py                 # Windows wlanapi engine & portal authenticator
│   ├── gui.py                    # Tkinter settings & credential management GUI
│   ├── install.bat               # Windows installer script & shortcut creator
│   ├── task_manager.py           # Windows Task Scheduler XML event registrant
│   ├── uninstall.bat             # Complete Windows uninstaller & data wiper
│   └── Setup/
│       ├── build_installer.bat   # Inno Setup CLI compiler runner
│       └── setup.iss             # Inno Setup 6 installer wizard script
├── .gitignore                    # Git rules (excludes binaries, builds, credentials)
├── LICENSE.txt                   # Open-source non-commercial license & disclaimer
├── README.md                     # Documentation (this file)
└── requirements.txt              # Python runtime dependencies (requests, keyring)
```

---

## 🚀 How to Install & Setup

### Method 1: Setup Wizard Installer (Recommended)
1. Download **`CampusWifiLogin-Setup.exe`** from the [Latest Releases](https://github.com/) page.
2. Run `CampusWifiLogin-Setup.exe`.
   - *Note*: If Windows SmartScreen appears ("Windows protected your PC"), click **More info** ➔ **Run anyway** (standard for unsigned open-source binaries).
3. Follow the setup wizard. It will:
   - Install the application to `%LOCALAPPDATA%\Programs\CampusWifiLogin`.
   - Register the Windows Task Scheduler automatic background trigger.
   - Place a **Campus Wi-Fi Settings** shortcut in your Start Menu.
4. The Settings GUI will open automatically after installation. Enter your credentials and click **Save Settings**.

---

### Method 2: Running from Python Source
If you have Python 3.8+ installed:
```powershell
# 1. Clone repository
git clone https://github.com/your-username/CampusLogin.git
cd CampusLogin

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the installer script
cd Windows
.\install.bat
```

---

## 🖥️ How to Use & Configure

### First-Time Configuration
1. Open the **Campus Wi-Fi Settings** app from your Start Menu.
   *(Or launch via terminal: `CampusWifiLogin.exe --config`)*.
2. Fill in the following fields:
   - **Student ID / Username**: Your campus Wi-Fi account username.
   - **Password**: Your campus Wi-Fi password.
   - **Target Wi-Fi Networks (SSIDs)**: The Wi-Fi name(s) of your campus network, comma-separated (e.g. `University_WiFi, Campus_Student`). If left empty, it will attempt login on any captive network detected.
   - **Portal Host**: The captive portal server address (defaults to `192.168.100.1:6082`, standard for Palo Alto Networks portals).
   - **Enable auto-login trigger**: Keep checked to ensure automatic background authentication on Wi-Fi connection.
3. Click **Save Settings**.

### Testing Your Login
- Click the **Test Login** button in the Settings GUI, or run:
  ```powershell
  CampusWifiLogin.exe --test
  ```
The app will probe the captive portal and submit credentials immediately, displaying real-time feedback.

---

## ⌨️ Command-Line Usage (CLI)

Both the compiled binary and Python script accept the following flags:

| Flag | Shorthand | Description |
| :--- | :--- | :--- |
| `--config` | `-c`, `--gui` | Opens the graphical Settings configuration window |
| `--test` | `-t` | Probes network status and executes a test login once |
| `--install` | `-i` | Registers the background event trigger with Windows Task Scheduler |
| `--uninstall`| `-u` | Unregisters background triggers and purges all saved data/credentials |
| *(no args)* | — | Runs silent background check & login (used by Task Scheduler) |

---

## 🗑️ How to Completely Delete / Uninstall

If you wish to remove the application, background tasks, configuration files, and saved passwords:

### Option 1: Via Windows Settings
Open `Settings ➔ Apps ➔ Installed apps ➔ Campus Wi-Fi Auto-Login ➔ Uninstall`.

### Option 2: Via Uninstaller Script
Run `Windows\uninstall.bat` or execute:
```powershell
CampusWifiLogin.exe --uninstall
```

### Option 3: Via Settings GUI
Open **Campus Wi-Fi Settings** and click the red **Uninstall / Reset** button.

### Manual Cleanup (if needed)
```powershell
# Delete scheduled background task
schtasks /Delete /TN "CampusWifiLogin" /F

# Remove local application files
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\CampusWifiLogin"
Remove-Item -Recurse -Force "$env:APPDATA\CampusWifiLogin"
Remove-Item "$([Environment]::GetFolderPath('Programs'))\Campus Wi-Fi Settings.lnk"
```
*(Credentials are automatically deleted from Windows Credential Manager).*

---

## 📦 How to Distribute Setup (For Maintainers)

When releasing this open-source project to other students or the public, **do not commit `.exe` files directly into git history**. Instead, use the GitHub Releases workflow:

### 1. Automated Releases via GitHub Actions (Recommended)
This repository includes a pre-configured GitHub Actions workflow in `.github/workflows/build.yml`.
Whenever you create and push a git version tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```
GitHub Actions will automatically:
1. Spin up a clean Windows runner.
2. Compile `CampusWifiLogin.exe` with Nuitka.
3. Build the Inno Setup installer wizard (`CampusWifiLogin-Setup.exe`).
4. Create a new **GitHub Release** and upload both the installer and portable `.exe` as release assets!

### 2. Manual Local Compilation & Distribution
If you prefer building locally:
1. Compile the executable:
   ```cmd
   cd Windows
   build_nuitka.bat
   ```
2. Build the Inno Setup installer:
   ```cmd
   cd Setup
   build_installer.bat
   ```
3. Go to GitHub ➔ **Releases** ➔ **Draft a new release**, and upload `Windows\Setup\CampusWifiLogin-Setup.exe`.

### 3. Windows SmartScreen Notice
Because open-source projects typically do not have \$300+/year EV code signing certificates from Microsoft:
- Windows will show *"Windows protected your PC"*.
- Tell users to click **"More info" ➔ "Run anyway"**.

---

## 🔨 Building from Source

### Prerequisites
- Python 3.8 or higher
- C/C++ compiler (MSVC or MinGW64) for Nuitka
- Inno Setup 6 (optional, for compiling the setup wizard)

```powershell
# Clone the repository
git clone https://github.com/your-username/CampusLogin.git
cd CampusLogin

# Install Python requirements
pip install -r requirements.txt
pip install nuitka
```

---

## 🔒 Security & Credential Storage

Your credentials are treated with the highest security standards:
- **Zero Plaintext Storage**: The JSON configuration file (`config.json`) only stores public settings such as your target SSIDs and portal host. It **never** contains your username or password.
- **Hardware-Backed Keyrings**: Passwords are saved directly into **Windows Credential Manager** via `keyring`.
- **Local Execution**: The application makes HTTP requests **strictly** to your local campus captive portal gateway and public connectivity probe endpoints (`connectivitycheck.gstatic.com`, `msftconnecttest.com`). No telemetry or user data is ever sent to third-party servers.

---

## ❓ Troubleshooting & FAQs

#### Q: The login does not trigger automatically on Wi-Fi connection.
- Check if your campus Wi-Fi SSID matches the name saved in **Campus Wi-Fi Settings**.
- Make sure "Enable auto-login trigger" is enabled in Settings.
- Verify that the `CampusWifiLogin` task exists in Windows Task Scheduler (`taskschd.msc`).

#### Q: The portal IP address or port is different at my university.
- Open **Campus Wi-Fi Settings** and update the **Portal Host** field (e.g. `portal.mycampus.edu:6082` or `10.0.0.1:8080`).

#### Q: My password changed and the app fails to authenticate.
- Launch **Campus Wi-Fi Settings**, enter your new password, and click **Save Settings**.

---

## 🗺️ Roadmap
- [ ] macOS support (`launchd` & Keychain)
- [ ] Linux support (`systemd` & SecretService)

---

## 📄 License

This project is licensed under the **Personal & Educational Non-Commercial License**. See the full [LICENSE.txt](LICENSE.txt) file for details.

```text
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
THE AUTHORS ASSUME NO RESPONSIBILITY FOR ANY POLICY VIOLATIONS OR ACCOUNT DISCIPLINARY ACTIONS.
COMMERCIAL DISTRIBUTION OR SALE IS STRICTLY PROHIBITED.
```
