import json
import os
from pathlib import Path
import keyring

SERVICE_NAME = "CampusWifiLogin"

DEFAULT_CONFIG = {
    "portal_host": "192.168.100.1:6082",
    "allowed_ssids": [],
    "probe_urls": [
        "http://www.msftconnecttest.com/connecttest.txt",
        "http://connectivitycheck.gstatic.com/generate_204",
    ],
    "direct_ip_probe": "http://1.1.1.1",
    "connect_timeout": 1.5,
    "read_timeout": 2.5,
    "max_attempts": 5,
    "initial_backoff": 1.0,
    "max_backoff": 3.0,
}


def get_config_dir():
    base_dir = os.environ.get("APPDATA")
    if not base_dir:
        base_dir = str(Path.home() / "AppData" / "Roaming")
    cfg_dir = Path(base_dir) / "CampusWifiLogin"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


def get_config_file():
    return get_config_dir() / "config.json"


def load_config():
    cfg_file = get_config_file()
    cfg = dict(DEFAULT_CONFIG)
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    cfg.update(saved)
        except Exception:
            pass
    return cfg


def save_config(cfg_data):
    cfg_file = get_config_file()
    current = load_config()
    current.update(cfg_data)
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4)


def get_credentials():
    try:
        user = keyring.get_password(SERVICE_NAME, "__active_user__")
        if not user:
            return None, None
        pwd = keyring.get_password(SERVICE_NAME, user)
        return user, pwd
    except Exception:
        return None, None


def save_credentials(username, password):
    if not username:
        return False
    try:
        keyring.set_password(SERVICE_NAME, "__active_user__", username)
        keyring.set_password(SERVICE_NAME, username, password if password else "")
        return True
    except Exception:
        return False


def is_configured():
    user, pwd = get_credentials()
    return bool(user and pwd)


def clear_credentials():
    try:
        user = keyring.get_password(SERVICE_NAME, "__active_user__")
        if user:
            try:
                keyring.delete_password(SERVICE_NAME, user)
            except Exception:
                pass
        try:
            keyring.delete_password(SERVICE_NAME, "__active_user__")
        except Exception:
            pass
        return True
    except Exception:
        return False


def clear_all_data():
    clear_credentials()
    try:
        cfg_dir = get_config_dir()
        if cfg_dir.exists():
            import shutil
            shutil.rmtree(cfg_dir, ignore_errors=True)
        return True
    except Exception:
        return False
