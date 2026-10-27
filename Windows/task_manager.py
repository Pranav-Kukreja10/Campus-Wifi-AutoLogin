import os
from pathlib import Path
import subprocess
import sys
import tempfile

TASK_NAME = "CampusWifiLogin"

TASK_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Auto-login to campus captive portal on Wi-Fi connection</Description>
  </RegistrationInfo>
  <Triggers>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Microsoft-Windows-NetworkProfile/Operational"&gt;&lt;Select Path="Microsoft-Windows-NetworkProfile/Operational"&gt;*[System[(EventID=10000)]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
    </EventTrigger>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Microsoft-Windows-WLAN-AutoConfig/Operational"&gt;&lt;Select Path="Microsoft-Windows-WLAN-AutoConfig/Operational"&gt;*[System[(EventID=8001)]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
    </EventTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{COMMAND}</Command>
      <Arguments>{ARGUMENTS}</Arguments>
      <WorkingDirectory>{WORKDIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def is_task_registered():
    try:
        res = subprocess.run(
            ["schtasks", "/Query", "/TN", TASK_NAME],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return res.returncode == 0
    except Exception:
        return False


def _get_compiled_exe_path():
    candidates = [
        os.environ.get("NUITKA_ONEFILE_BINARY"),
        sys.argv[0] if sys.argv else None,
    ]
    for cand in candidates:
        if not cand:
            continue
        try:
            p = Path(cand).resolve()
            if p.suffix.lower() == ".exe" and p.exists() and "onefile_" not in str(p.parent).lower():
                return str(p)
        except Exception:
            pass

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        installed = Path(local_app_data) / "Programs" / "CampusWifiLogin" / "CampusWifiLogin.exe"
        if installed.exists():
            return str(installed)
    return None


def _is_compiled():
    return "__compiled__" in globals() or getattr(sys, "frozen", False) or bool(
        os.environ.get("NUITKA_ONEFILE_BINARY")
    )


def register_task(executable_path=None, script_path=None):
    if executable_path:
        cmd = str(executable_path)
        args = ""
        workdir = str(Path(executable_path).parent)
    else:
        onefile_exe = _get_compiled_exe_path() if _is_compiled() or str(sys.argv[0]).lower().endswith(".exe") else None
        if onefile_exe:
            cmd = onefile_exe
            args = ""
            workdir = str(Path(onefile_exe).parent)
        elif getattr(sys, "frozen", False):
            cmd = sys.executable
            args = ""
            workdir = str(Path(sys.executable).parent)
        else:
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            cmd = str(pythonw if pythonw.exists() else sys.executable)
            target_script = script_path or Path(__file__).with_name("captive_portal_login.py").resolve()
            args = f'"{target_script}"'
            workdir = str(Path(target_script).parent)

    xml_content = TASK_XML_TEMPLATE.format(
        COMMAND=cmd,
        ARGUMENTS=args,
        WORKDIR=workdir,
    )

    with tempfile.NamedTemporaryFile("w", encoding="utf-16", suffix=".xml", delete=False) as f:
        temp_xml = f.name
        f.write(xml_content)

    try:
        res = subprocess.run(
            ["schtasks", "/Create", "/TN", TASK_NAME, "/XML", temp_xml, "/F"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return res.returncode == 0, res.stdout or res.stderr
    finally:
        try:
            os.remove(temp_xml)
        except Exception:
            pass


def unregister_task():
    try:
        res = subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return res.returncode == 0
    except Exception:
        return False
