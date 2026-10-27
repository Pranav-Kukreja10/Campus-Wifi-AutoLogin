# Campus Wi-Fi Auto-Login

[![License](https://img.shields.io/badge/License-Non--Commercial-blue.svg)](LICENSE.txt)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](README.md)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/Build-GitHub%20Actions-brightgreen.svg)](.github/workflows/build.yml)

An automated, cross-platform background authentication utility for university and campus captive Wi-Fi portals (such as Palo Alto Networks, Fortinet, SonicWall, and Aruba portals) across **Windows 10/11**, **macOS**, and **Linux**.

Whenever your computer reconnects to campus Wi-Fi or wakes from sleep, **Campus Wi-Fi Auto-Login** detects the network state event and authenticates in the background in milliseconds—without opening annoying browser tabs or requiring you to re-type credentials throughout the day.

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
- [Repository Organization](#-repository-organization)
- [How to Install & Setup](#-how-to-install--setup)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [How to Use & Configure](#-how-to-use--configure)
- [Command-Line Usage (CLI)](#-command-line-usage-cli)
- [How to Completely Delete / Uninstall](#-how-to-completely-delete--uninstall)
- [How to Distribute Setup (For Maintainers)](#-how-to-distribute-setup-for-maintainers)
- [Building from Source](#-building-from-source)
- [Security & Credential Storage](#-security--credential-storage)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)
- [License](#-license)

---

## ✨ Features

- ⚡ **Zero-Battery, Event-Driven**: Does **not** run a heavy polling loop in the background. Instead, it hooks directly into native OS network event triggers (Windows Task Scheduler, macOS `launchd`, Linux `systemd`).
- 🔐 **Military-Grade Credential Protection**: Passwords are never stored in plaintext configuration files. They are encrypted and stored in your operating system's native hardware-backed vault via Python `keyring`:
  - **Windows**: Windows Credential Manager
  - **macOS**: Apple Keychain
  - **Linux**: SecretService / GNOME Keyring / KWallet
- 🖥️ **Modern Desktop GUI**: Includes an intuitive Tkinter dark-themed interface to configure your credentials, target Wi-Fi SSIDs, and portal addresses with one click.
- 🔒 **Process Lock Concurrency Control**: Uses native file locking (`msvcrt` on Windows, `fcntl` on Unix) to prevent race conditions or duplicate login submissions if multiple network interfaces cycle simultaneously.
- 🎯 **Target SSID Whitelisting**: Automatically identifies your active Wi-Fi network and only attempts authentication when connected to authorized campus SSIDs (or all networks if left unrestricted).
- 🧹 **One-Click Total Wipe**: Offers clean uninstallation that purges all scheduled tasks, desktop shortcuts, configurations, and stored credentials with zero leftover registry clutter.

---

## ⚙️ How It Works

```
                       +-----------------------------+
                       | Wi-Fi Connects / Reconnects |
                       +--------------+--------------+
                                      |
              +-----------------------+-----------------------+
              | (Native OS Network State Change Trigger)      |
              v                       v                       v
     [Windows Task Scheduler]   [macOS launchd]      [Linux systemd]
      (EventID 10000 / 8001)    (Airport plist watch) (Timer / Network)
              |                       |                       |
              +-----------------------+-----------------------+
                                      |
                                      v
                        +---------------------------+
                        | captive_portal_login.py   |
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

## 📁 Repository Organization

```text
CampusLogin/
├── .github/
│   └── workflows/
│       └── build.yml             # GitHub Actions CI/CD (Multi-platform compile & auto-release)
├── Linux/
│   ├── app_icon.png              # Linux application launcher icon
│   ├── build_linux.sh            # Nuitka standalone binary compiler
│   ├── captive_portal_login.py   # CLI entry point & background controller
│   ├── config_manager.py         # JSON settings & Keyring credential manager
│   ├── engine.py                 # Network detection, probe & portal HTTP engine
│   ├── gui.py                    # Tkinter settings & credential management GUI
│   ├── install.sh                # Linux installer script & desktop entry generator
│   ├── main.py                   # Minimal application launcher
│   ├── task_manager.py           # systemd user service and timer manager
│   └── uninstall.sh              # Complete Linux uninstaller & data wiper
├── MacOS/
│   ├── app_icon.png              # macOS application icon
│   ├── build_macos.sh            # Nuitka macOS .app bundle compiler
│   ├── captive_portal_login.py   # CLI entry point & background controller
│   ├── config_manager.py         # macOS settings & Apple Keychain manager
│   ├── engine.py                 # macOS network & captive portal engine
│   ├── gui.py                    # Tkinter configuration GUI
│   ├── Install.command           # Double-clickable installer launcher for Finder
│   ├── install.sh                # macOS installer & launchd plist generator
│   ├── main.py                   # Minimal application launcher
│   ├── task_manager.py           # launchd LaunchAgent service controller
│   ├── Uninstall.command         # Double-clickable uninstaller launcher
│   ├── uninstall.sh              # Complete macOS uninstaller & data wiper
│   └── Setup/
│       ├── build_dmg.sh          # Native hdiutil DMG disk image generator
│       ├── build_pkg.sh          # Native pkgbuild/productbuild PKG installer generator
│       ├── Distribution.xml      # macOS Installer distribution manifest
│       └── scripts/postinstall   # PKG post-install configuration script
├── Windows/
│   ├── app_icon.ico              # Windows multi-resolution application icon
│   ├── app_icon.png              # High-resolution PNG icon
│   ├── build_nuitka.bat          # Nuitka Windows standalone compiler
│   ├── captive_portal_login.py   # CLI entry point & background controller
│   ├── config_manager.py         # Windows settings & Credential Manager handler
│   ├── engine.py                 # Windows wlanapi engine & portal authenticator
│   ├── gui.py                    # Tkinter configuration GUI
│   ├── install.bat               # Windows installer script & shortcut creator
│   ├── main.py                   # Minimal application launcher
│   ├── task_manager.py           # Windows Task Scheduler XML event registrant
│   ├── uninstall.bat             # Complete Windows uninstaller & data wiper
│   └── Setup/
│       ├── build_installer.bat   # Inno Setup CLI compiler runner
│       └── setup.iss             # Inno Setup 6 installer wizard script
├── .gitignore                    # Git rules (excludes binaries, builds, credentials)
├── LICENSE.txt                   # Open-source non-commercial license & disclaimer
├── README.md                     # Comprehensive documentation (this file)
└── requirements.txt              # Python runtime dependencies (requests, keyring)
```

---

## 🚀 How to Install & Setup

### Windows

#### Method 1: Pre-Built Setup Wizard (Recommended)
1. Download **`CampusWifiLogin-Setup.exe`** from the [Latest Releases](https://github.com/) page.
2. Run `CampusWifiLogin-Setup.exe`.
   - *Note*: If Windows SmartScreen appears ("Windows protected your PC"), click **More info** ➔ **Run anyway** (this appears for unsigned open-source binaries).
3. Follow the setup wizard. It will:
   - Install the application to `%LOCALAPPDATA%\Programs\CampusWifiLogin`.
   - Register the Windows Task Scheduler automatic background trigger.
   - Place a **Campus Wi-Fi Settings** shortcut in your Start Menu.
4. The Settings GUI will open automatically after installation. Enter your credentials and click **Save Settings**.

#### Method 2: Running from Source
If you have Python 3.8+ installed:
```powershell
# 1. Clone the repository
git clone https://github.com/your-username/CampusLogin.git
cd CampusLogin

# 2. Install requirements
pip install -r requirements.txt

# 3. Run the Windows installer script
cd Windows
.\install.bat
```

---

### macOS

#### Method 1: Using Installer Packages (.dmg or .pkg)
1. Download **`CampusWifiLogin.dmg`** or **`CampusWifiLogin-Setup.pkg`** from Releases.
2. Double-click to open and follow the installation instructions.
   - *Note*: If macOS blocks execution with *"Cannot verify developer"*, right-click the file ➔ select **Open** ➔ click **Open** in the dialog, or permit it in **System Settings ➔ Privacy & Security**.

#### Method 2: Running from Source / Terminal
```bash
# 1. Clone repository
git clone https://github.com/your-username/CampusLogin.git
cd CampusLogin/MacOS

# 2. Make scripts executable and run
chmod +x install.sh
./install.sh
```
*(Alternatively, simply double-click `Install.command` in Finder).*

The installer registers a user LaunchAgent (`com.campuswifi.autologin.plist`) under `~/Library/LaunchAgents/` and immediately opens the Settings GUI.

---

### Linux

```bash
# 1. Clone repository
git clone https://github.com/your-username/CampusLogin.git
cd CampusLogin/Linux

# 2. Ensure Python 3 and Tkinter are present
# Debian/Ubuntu: sudo apt install python3 python3-tk python3-pip
# Fedora:        sudo dnf install python3 python3-tkinter python3-pip
# Arch Linux:    sudo pacman -S python python-requests tk

# 3. Run installer
chmod +x install.sh
./install.sh
```
The Linux installer copies files to `~/.local/share/CampusWifiLogin/`, installs a desktop launcher (`campuswifi-login.desktop`), enables a `systemd` user service and timer, and launches the configuration window.

---

## 🖥️ How to Use & Configure

### First-Time Configuration
1. Open the **Campus Wi-Fi Settings** app from your Start Menu, Spotlight, or Application Launcher.
   *(Or launch via terminal: `python captive_portal_login.py --config`)*.
2. Fill in the following fields:
   - **Student ID / Username**: Your campus Wi-Fi account username.
   - **Password**: Your campus Wi-Fi password.
   - **Target Wi-Fi Networks (SSIDs)**: The Wi-Fi name(s) of your campus network, comma-separated (e.g. `University_WiFi, Campus_Student`). If left empty, it will attempt login on any captive network detected.
   - **Portal Host**: The captive portal server address (defaults to `192.168.100.1:6082`, standard for Palo Alto Networks portals).
   - **Enable auto-login trigger**: Keep checked to ensure automatic background authentication on Wi-Fi connection.
3. Click **Save Settings**.

### Testing Your Login
- Click the **Test Login** button in the Settings GUI, or run:
  ```bash
  # Windows
  CampusWifiLogin.exe --test

  # macOS / Linux
  python3 captive_portal_login.py --test
  ```
The app will probe the captive portal and submit credentials immediately, displaying real-time feedback.

---

## ⌨️ Command-Line Usage (CLI)

Both the compiled binaries and Python scripts accept the following flags:

| Flag | Shorthand | Description |
| :--- | :--- | :--- |
| `--config` | `-c`, `--gui` | Opens the graphical Settings configuration window |
| `--test` | `-t` | Probes network status and executes a test login once |
| `--install` | `-i` | Registers the background event trigger with the operating system |
| `--uninstall`| `-u` | Unregisters background triggers and purges all saved data/credentials |
| *(no args)* | — | Runs silent background check & login (used by Task Scheduler/launchd/systemd) |

---

## 🗑️ How to Completely Delete / Uninstall

If you wish to remove the application, all background tasks, configuration files, and saved passwords, follow these instructions:

### Windows
- **Via Windows Settings**: Open `Settings ➔ Apps ➔ Installed apps ➔ Campus Wi-Fi Auto-Login ➔ Uninstall`.
- **Via Uninstaller Script**: Run `Windows\uninstall.bat`.
- **Via Settings GUI**: Click the red **Uninstall / Reset** button in the app.
- **Manual Cleanup (if needed)**:
  ```powershell
  # Delete scheduled background task
  schtasks /Delete /TN "CampusWifiLogin" /F

  # Remove local files
  Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\CampusWifiLogin"
  Remove-Item -Recurse -Force "$env:APPDATA\CampusWifiLogin"
  Remove-Item "$([Environment]::GetFolderPath('Programs'))\Campus Wi-Fi Settings.lnk"
  ```
  *(Credentials are automatically deleted from Windows Credential Manager).*

### macOS
- **Via Uninstaller Script**: Open terminal in `MacOS/` and run `./uninstall.sh` (or double-click `Uninstall.command`).
- **Via Settings GUI**: Click **Uninstall / Reset** in the app.
- **Manual Cleanup (if needed)**:
  ```bash
  # Unload and remove LaunchAgent
  launchctl unload ~/Library/LaunchAgents/com.campuswifi.autologin.plist 2>/dev/null
  rm -f ~/Library/LaunchAgents/com.campuswifi.autologin.plist

  # Remove application files and configurations
  rm -rf "$HOME/Library/Application Support/CampusWifiLogin"
  ```
  *(Credentials are automatically deleted from Apple Keychain).*

### Linux
- **Via Uninstaller Script**: Open terminal in `Linux/` and run `./uninstall.sh`.
- **Via Settings GUI**: Click **Uninstall / Reset** in the app.
- **Manual Cleanup (if needed)**:
  ```bash
  # Stop and disable systemd service
  systemctl --user stop campuswifi_autologin.timer 2>/dev/null
  systemctl --user disable campuswifi_autologin.timer 2>/dev/null
  rm -f ~/.config/systemd/user/campuswifi_autologin.*

  # Remove application data, desktop entry & config
  rm -rf ~/.local/share/CampusWifiLogin
  rm -f ~/.local/share/applications/campuswifi-login.desktop
  rm -rf ~/.config/CampusWifiLogin
  ```

---

## 📦 How to Distribute Setup (For Maintainers)

When releasing this open-source project to other students or the public, **do not commit `.exe` or binary files directly to git**. Instead, use the GitHub Releases workflow:

### 1. Automated Releases via GitHub Actions (Recommended)
This repository includes a pre-configured GitHub Actions workflow in `.github/workflows/build.yml`.
Whenever you create and push a git version tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```
GitHub Actions will automatically:
1. Spin up clean Windows, macOS, and Linux runners.
2. Compile standalone binaries with Nuitka.
3. Build the Windows Inno Setup installer (`CampusWifiLogin-Setup.exe`).
4. Package macOS `.app` bundle into a `.zip` and Linux into a `.tar.gz`.
5. Create a new **GitHub Release** and upload all installable assets automatically!

### 2. Manual Local Compilation & Distribution
If you prefer building locally:

- **Windows Installer**:
  1. Compile the binary: `cd Windows && .\build_nuitka.bat`
  2. Build the installer: `cd Setup && .\build_installer.bat`
  3. Upload `CampusWifiLogin-Setup.exe` to GitHub Releases.
- **macOS Installer**:
  1. `cd MacOS/Setup && ./build_dmg.sh` (produces `CampusWifiLogin.dmg`).
  2. Upload `CampusWifiLogin.dmg` to GitHub Releases.
- **Linux Distribution**:
  1. `cd Linux && ./build_linux.sh`
  2. Package with `tar -czvf CampusWifiLogin-Linux.tar.gz CampusWifiLogin app_icon.png install.sh uninstall.sh`.

### 3. Dealing with Windows SmartScreen & macOS Gatekeeper
Because open-source projects typically do not have \$300+/year EV code signing certificates from Microsoft or Apple:
- **Windows users** will see *"Windows protected your PC"*. Advise users to click **"More info" ➔ "Run anyway"**.
- **macOS users** will see *"macOS cannot verify the developer"*. Advise users to **Right-click ➔ Open**, or allow it under **System Settings ➔ Privacy & Security**.

---

## 🔨 Building from Source

### Prerequisites
- Python 3.8 or higher
- C/C++ compiler (GCC / Clang / MSVC) for Nuitka
- Inno Setup 6 (optional, for compiling Windows Setup wizard)

```bash
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
- **Hardware-Backed Keyrings**: Passwords are saved directly into the operating system's native secure store (`keyring`), protected by your OS user account credentials and encryption.
- **Local Execution**: The application makes HTTP requests **strictly** to your local campus captive portal gateway and public connectivity probe endpoints (`connectivitycheck.gstatic.com`, `msftconnecttest.com`). No telemetry or user data is ever sent to third-party servers.

---

## ❓ Troubleshooting & FAQs

#### Q: The login does not trigger automatically on Wi-Fi connection.
- Check if your campus Wi-Fi SSID matches the name saved in **Campus Wi-Fi Settings**.
- Make sure "Enable auto-login trigger" is enabled in Settings.
- On Windows, verify that the `CampusWifiLogin` task exists in Windows Task Scheduler (`taskschd.msc`).
- On macOS, verify the agent status via `launchctl list | grep campuswifi`.

#### Q: The portal IP address or port is different at my university.
- Open **Campus Wi-Fi Settings** and update the **Portal Host** field (e.g. `portal.mycampus.edu:6082` or `10.0.0.1:8080`).

#### Q: My password changed and the app fails to authenticate.
- Launch **Campus Wi-Fi Settings**, enter your new password, and click **Save Settings**.

---

## 📄 License

This project is licensed under the **Personal & Educational Non-Commercial License**. See the full [LICENSE.txt](LICENSE.txt) file for details.

```text
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
THE AUTHORS ASSUME NO RESPONSIBILITY FOR ANY POLICY VIOLATIONS OR ACCOUNT DISCIPLINARY ACTIONS.
COMMERCIAL DISTRIBUTION OR SALE IS STRICTLY PROHIBITED.
```
