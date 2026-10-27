import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlparse

import requests

from config_manager import get_credentials, is_configured, load_config

MUTEX_NAME = "Local\\CaptivePortalLoginMutex"
_mutex_handle = None

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


def acquire_lock():
    global _mutex_handle
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
        if not handle:
            return True
        last_err = kernel32.GetLastError()
        if last_err == 183:
            kernel32.CloseHandle(handle)
            return False
        _mutex_handle = handle
        return True
    except Exception:
        return True


def release_lock():
    global _mutex_handle
    if _mutex_handle:
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.ReleaseMutex(_mutex_handle)
            kernel32.CloseHandle(_mutex_handle)
        except Exception:
            pass
        _mutex_handle = None


class DOT11_SSID(ctypes.Structure):
    _fields_ = [("uSSIDLength", ctypes.c_ulong), ("ucSSID", ctypes.c_char * 32)]


class WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [
        ("InterfaceGuid", ctypes.c_ubyte * 16),
        ("strInterfaceDescription", ctypes.c_wchar * 256),
        ("isState", ctypes.c_uint),
    ]


class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
    _fields_ = [
        ("dwNumberOfItems", ctypes.c_uint),
        ("dwIndex", ctypes.c_uint),
        ("InterfaceInfo", WLAN_INTERFACE_INFO * 1),
    ]


class WLAN_CONNECTION_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("isState", ctypes.c_uint),
        ("wlanConnectionMode", ctypes.c_uint),
        ("strProfileName", ctypes.c_wchar * 256),
        ("dot11Ssid", DOT11_SSID),
    ]


def _get_ssid_ctypes():
    try:
        wlan = ctypes.windll.wlanapi
        handle = wintypes.HANDLE()
        negotiated_version = wintypes.DWORD()
        ret = wlan.WlanOpenHandle(2, None, ctypes.byref(negotiated_version), ctypes.byref(handle))
        if ret != 0:
            return None
        try:
            pList = ctypes.c_void_p()
            ret = wlan.WlanEnumInterfaces(handle, None, ctypes.byref(pList))
            if ret == 0 and pList:
                try:
                    info_list = ctypes.cast(pList, ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)).contents
                    for i in range(info_list.dwNumberOfItems):
                        guid = info_list.InterfaceInfo[i].InterfaceGuid
                        pData = ctypes.c_void_p()
                        dataSize = wintypes.DWORD()
                        ret = wlan.WlanQueryInterface(
                            handle,
                            ctypes.byref(guid),
                            7,
                            None,
                            ctypes.byref(dataSize),
                            ctypes.byref(pData),
                            None,
                        )
                        if ret == 0 and pData:
                            try:
                                conn = ctypes.cast(pData, ctypes.POINTER(WLAN_CONNECTION_ATTRIBUTES)).contents
                                if conn.isState == 1:
                                    ssid_len = conn.dot11Ssid.uSSIDLength
                                    if 0 < ssid_len <= 32:
                                        return conn.dot11Ssid.ucSSID[:ssid_len].decode("utf-8", errors="ignore")
                            finally:
                                wlan.WlanFreeMemory(pData)
                finally:
                    wlan.WlanFreeMemory(pList)
        finally:
            wlan.WlanCloseHandle(handle, None)
    except Exception:
        pass
    return None


def _get_ssid_netsh():
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            text=True,
            timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("SSID") and not line.startswith("SSID BSSID"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    except Exception:
        pass
    return None


def get_current_ssid():
    ssid = _get_ssid_ctypes()
    if ssid:
        return ssid
    return _get_ssid_netsh()


def detect_portal(session, config):
    portal_host = config.get("portal_host", "")
    probe_urls = config.get("probe_urls", [])
    direct_ip = config.get("direct_ip_probe", "")
    timeout = (config.get("connect_timeout", 1.5), config.get("read_timeout", 2.5))

    dns_failed = False
    for probe in probe_urls:
        try:
            # stream=True avoids downloading payload if already online
            resp = session.get(probe, timeout=timeout, allow_redirects=True, verify=False, stream=True)
        except requests.exceptions.ConnectionError as e:
            err_str = str(e)
            if "NameResolutionError" in err_str or "getaddrinfo failed" in err_str:
                dns_failed = True
                break
            continue
        except requests.RequestException:
            continue

        final_url = resp.url
        # 1. Fast portal detection via redirect URL
        if portal_host and portal_host in final_url and "uid.php" in final_url:
            return final_url, resp.text

        # 2. HTTP 204 (Google) is definitive proof of internet connectivity with 0 bytes downloaded
        if resp.status_code == 204 and (not portal_host or portal_host not in final_url):
            return None, None

        # 3. HTTP 200: check if captive portal served HTML page without redirecting
        if resp.status_code == 200:
            text = resp.text
            if "login_form" in text or "Authentication Portal" in text:
                return final_url, text
            return None, None

        return None, None

    # Fallback to direct IP if Windows DNS resolver has not settled yet
    if dns_failed and direct_ip:
        try:
            resp = session.get(direct_ip, timeout=timeout, allow_redirects=True, verify=False, stream=True)
            final_url = resp.url
            if portal_host and portal_host in final_url and "uid.php" in final_url:
                return final_url, resp.text
            text = resp.text
            if "login_form" in text or "Authentication Portal" in text:
                return final_url, text
        except requests.RequestException:
            pass

    return "RETRY", None


def parse_login_params(login_url, html_text="", fallback_url=""):
    parsed = urlparse(login_url)
    qs = parse_qs(parsed.query)
    params = {k: v[0] for k, v in qs.items()}

    if "token" not in params and html_text:
        for field in ("vsys", "rule", "token", "preauthid", "url"):
            m = re.search(rf'name=["\']{field}["\']\s+value=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            if m:
                params[field] = m.group(1)

    params.setdefault("vsys", "1")
    params.setdefault("rule", "1")
    params.setdefault("url", fallback_url or "http://www.msftconnecttest.com/connecttest.txt")

    if "token" not in params:
        return None

    return params


AUTH_FAIL_PHRASES = (
    "invalid user",
    "invalid password",
    "incorrect user",
    "incorrect password",
    "authentication failed",
    "user authentication failed",
    "login failed",
    "bad username or password",
    "credentials are invalid",
    "access denied",
    "account is locked",
)


def submit_login(session, params, config, username, password, login_url=None):
    portal_host = config.get("portal_host", "")
    timeout = (config.get("connect_timeout", 1.5), config.get("read_timeout", 2.5))
    post_url = f"https://{portal_host}/php/uid.php"
    escaped_user = username.replace("\\", "\\\\")

    form_data = {
        "inputStr": "",
        "escapeUser": escaped_user,
        "preauthid": params.get("preauthid", ""),
        "user": username,
        "passwd": password,
        "ok": "Login",
    }

    # Browser-grade form navigation & origin headers
    origin = f"https://{portal_host}"
    post_headers = {
        "Origin": origin,
        "Referer": login_url or f"{origin}/php/uid.php",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        resp = session.post(
            post_url,
            params=params,
            data=form_data,
            headers=post_headers,
            timeout=timeout,
            verify=False,
            allow_redirects=False,
        )
    except requests.RequestException:
        return False, False  # (submitted, auth_failed)

    # 1. HTTP 401/403 directly indicates credential rejection
    if resp.status_code in (401, 403):
        return False, True

    # 2. Check for explicit error messages in response HTML
    resp_text_lower = resp.text.lower() if resp.text else ""
    for phrase in AUTH_FAIL_PHRASES:
        if phrase in resp_text_lower:
            return False, True

    # 3. Check for error flags in redirect headers
    location = resp.headers.get("Location", "").lower()
    if "error=" in location or "status=fail" in location or "auth_failed" in location:
        return False, True

    return resp.ok, False


def confirm_online(session, config):
    probe_urls = config.get("probe_urls", [])
    portal_host = config.get("portal_host", "")
    timeout = (config.get("connect_timeout", 1.5), config.get("read_timeout", 2.5))

    for probe in probe_urls:
        for attempt in range(2):
            try:
                resp = session.get(probe, timeout=timeout, stream=True, allow_redirects=True, verify=False)
                if portal_host not in resp.url and (resp.status_code in (200, 204)):
                    return True
            except requests.RequestException:
                pass
            if attempt == 0:
                time.sleep(0.15)
    return False


def run_once(session, config, username, password):
    login_url, html_text = detect_portal(session, config)

    if login_url is None:
        return True, False  # (online, auth_failed)

    if login_url == "RETRY":
        return False, False

    probe_urls = config.get("probe_urls", [])
    fallback_url = probe_urls[0] if probe_urls else ""
    params = parse_login_params(login_url, html_text, fallback_url)
    if not params:
        return False, False

    submitted, auth_failed = submit_login(
        session, params, config, username, password, login_url=login_url
    )
    if auth_failed:
        return False, True

    if submitted and confirm_online(session, config):
        return True, False

    return False, False


def execute_auto_login(ignore_ssid=False):
    if not acquire_lock():
        return False

    try:
        # 1. Ultra-fast Win32 WLAN API query (<1ms)
        ssid = get_current_ssid()
        if ssid is None:
            # Brief 0.3s grace period for Windows WLAN association
            time.sleep(0.3)
            ssid = get_current_ssid()

        if ssid is None and not ignore_ssid:
            return False

        config = load_config()
        allowed_ssids = set(config.get("allowed_ssids", []))

        # 2. Fast-path exit for non-campus networks (Home Wi-Fi, Phone Hotspot, etc.)
        # Exits without touching Windows DPAPI or credential decryption
        if not ignore_ssid and allowed_ssids and ssid not in allowed_ssids:
            return False

        # 3. Only query Windows Credential Manager (DPAPI) when confirmed on campus network
        username, password = get_credentials()
        if not username or not password:
            return "AUTH_FAILED"

        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        max_attempts = int(config.get("max_attempts", 5))
        backoff = float(config.get("initial_backoff", 1.0))
        max_backoff = float(config.get("max_backoff", 3.0))

        portal_encountered = False
        for attempt in range(1, max_attempts + 1):
            is_online, auth_failed = run_once(session, config, username, password)
            if is_online:
                return True
            if auth_failed:
                # Abort immediately on bad credentials to prevent campus AD/LDAP lockout
                return "AUTH_FAILED"

            if attempt < max_attempts:
                time.sleep(backoff)
                backoff = min(backoff * 1.5, max_backoff)

        # Post-loop verification: if portal is still intercepting us despite attempts,
        # credentials were very likely rejected without an explicit error body.
        check_url, _ = detect_portal(session, config)
        if check_url and check_url != "RETRY":
            return "AUTH_FAILED"

        return False
    finally:
        release_lock()
