import os
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from config_manager import (
    clear_all_data,
    get_credentials,
    is_configured,
    load_config,
    save_config,
    save_credentials,
)
from engine import execute_auto_login, get_current_ssid
from task_manager import is_task_registered, register_task, unregister_task


class CampusLoginApp:
    def __init__(self, root, prompt_reauth=False):
        self.root = root
        self.prompt_reauth = prompt_reauth
        self.root.title("Campus Wi-Fi - Authentication Failed" if prompt_reauth else "Campus Wi-Fi Auto-Login Settings")
        self.root.geometry("580x705")
        self.root.minsize(540, 660)

        self._set_app_icon()
        self._apply_styles()
        self._build_ui()
        self._load_current_values()
        self._center_window()

        if self.prompt_reauth:
            self.root.after(150, self._handle_reauth_prompt)

    def _set_app_icon(self):
        """Set native window and taskbar icon."""
        try:
            import ctypes
            # Unlink from python.exe so Windows taskbar displays our custom Wi-Fi icon
            app_id = "campuswifi.autologin.client.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

        candidates = [
            Path(__file__).resolve().parent,
            Path(sys.executable).resolve().parent,
        ]
        onefile_bin = os.environ.get("NUITKA_ONEFILE_BINARY")
        if onefile_bin:
            candidates.append(Path(onefile_bin).resolve().parent)

        ico_path = None
        png_path = None
        for d in candidates:
            if not ico_path and (d / "app_icon.ico").exists():
                ico_path = d / "app_icon.ico"
            if not png_path and (d / "app_icon.png").exists():
                png_path = d / "app_icon.png"

        if ico_path and ico_path.exists():
            try:
                self.root.iconbitmap(str(ico_path))
            except Exception:
                pass

        if png_path and png_path.exists():
            try:
                self._photo_icon = tk.PhotoImage(file=str(png_path))
                self.root.iconphoto(True, self._photo_icon)
            except Exception:
                pass

    def _center_window(self):
        self.root.update_idletasks()
        w = 580
        h = 705
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 25)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _handle_reauth_prompt(self):
        self._set_status("Authentication failed! Please update your credentials.", color="#dc2626")
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(300, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass

        if hasattr(self, "entry_password"):
            self.entry_password.focus_set()
            self.entry_password.select_range(0, tk.END)

        messagebox.showerror(
            "Authentication Failed",
            "The campus Wi-Fi captive portal rejected your credentials.\n\nPlease verify and re-enter your username or password.",
            parent=self.root,
        )

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Windows 11 Modern Color Palette
        self.bg_color = "#f8fafc"        # Slate 50
        self.card_color = "#ffffff"      # Pure white
        self.border_color = "#e2e8f0"    # Slate 200
        self.text_primary = "#0f172a"    # Slate 900
        self.text_secondary = "#64748b"  # Slate 500
        self.primary_blue = "#2563eb"    # Blue 600
        self.primary_hover = "#1d4ed8"   # Blue 700
        self.badge_bg = "#f1f5f9"        # Slate 100

        self.root.configure(bg=self.bg_color)

        style.configure(".", background=self.bg_color, foreground=self.text_primary, font=("Segoe UI", 9))
        style.configure("TLabel", background=self.bg_color, foreground=self.text_primary)
        style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), foreground="#0f172a")
        style.configure("Subheader.TLabel", font=("Segoe UI", 9), foreground=self.text_secondary)
        style.configure("Section.TLabel", font=("Segoe UI", 10, "bold"), foreground="#1e293b", background=self.card_color)

        style.configure("Card.TFrame", background=self.card_color)
        style.configure("CardLabel.TLabel", background=self.card_color, foreground=self.text_primary, font=("Segoe UI", 9))
        style.configure("Badge.TFrame", background=self.badge_bg)

        # Inputs
        style.configure("TEntry", padding=6)

        # Primary Button (Save)
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 9, "bold"),
            background=self.primary_blue,
            foreground="#ffffff",
            padding=(16, 7),
            borderwidth=0,
        )
        style.map("Primary.TButton", background=[("active", self.primary_hover), ("disabled", "#94a3b8")])

        # Secondary Button (Test / Close / Add)
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 9),
            background="#ffffff",
            foreground="#1e293b",
            padding=(12, 6),
            borderwidth=1,
        )
        style.map("Secondary.TButton", background=[("active", "#f1f5f9")])

        # Danger / Uninstall Button
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 9),
            background="#ffffff",
            foreground="#dc2626",
            padding=(12, 6),
            borderwidth=1,
        )
        style.map("Danger.TButton", background=[("active", "#fef2f2")])

        # Checkbutton
        style.configure("TCheckbutton", background=self.card_color, font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[("active", self.card_color)])

    def _build_ui(self):
        main_container = tk.Frame(self.root, bg=self.bg_color, padx=18, pady=16)
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- Header Section ---
        header_frame = tk.Frame(main_container, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(header_frame, text="Campus Wi-Fi Auto-Login", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header_frame,
            text="Automatic captive portal login for university Wi-Fi.",
            style="Subheader.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        # --- Main Card ---
        card_outer = tk.Frame(
            main_container,
            bg=self.card_color,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=self.border_color,
            highlightcolor=self.border_color,
        )
        card_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        card = tk.Frame(card_outer, bg=self.card_color, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True)

        # 1. Account Credentials
        ttk.Label(card, text="Account Credentials", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 8))

        user_frame = tk.Frame(card, bg=self.card_color)
        user_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(user_frame, text="Username / Roll No:", width=18, anchor=tk.W, style="CardLabel.TLabel").pack(side=tk.LEFT)
        self.entry_username = ttk.Entry(user_frame, font=("Segoe UI", 9))
        self.entry_username.pack(side=tk.LEFT, fill=tk.X, expand=True)

        pass_frame = tk.Frame(card, bg=self.card_color)
        pass_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(pass_frame, text="Password:", width=18, anchor=tk.W, style="CardLabel.TLabel").pack(side=tk.LEFT)
        self.entry_password = ttk.Entry(pass_frame, show="•", font=("Segoe UI", 9))
        self.entry_password.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.show_pass_var = tk.BooleanVar(value=False)
        self.btn_show_pass = ttk.Checkbutton(
            pass_frame,
            text="Show",
            variable=self.show_pass_var,
            command=self._toggle_password,
            style="TCheckbutton",
        )
        self.btn_show_pass.pack(side=tk.LEFT, padx=(8, 0))

        # Separator
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # 2. Network Configuration
        ttk.Label(card, text="Network Configuration", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 8))

        host_frame = tk.Frame(card, bg=self.card_color)
        host_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(host_frame, text="Portal Host:", width=18, anchor=tk.W, style="CardLabel.TLabel").pack(side=tk.LEFT)
        self.entry_host = ttk.Entry(host_frame, font=("Segoe UI", 9))
        self.entry_host.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Allowed SSIDs with Scrollbar
        ssid_row = tk.Frame(card, bg=self.card_color)
        ssid_row.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        ttk.Label(
            ssid_row,
            text="Allowed SSIDs:\n(Lines or commas\nseperated)",
            width=18,
            anchor=tk.NW,
            style="CardLabel.TLabel",
        ).pack(side=tk.LEFT, anchor=tk.NW, pady=(4, 0))

        # Container with integrated border and scrollbar
        ssid_box_frame = tk.Frame(
            ssid_row,
            bg="#ffffff",
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor=self.primary_blue,
        )
        ssid_box_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.txt_ssids = tk.Text(
            ssid_box_frame,
            height=6,
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg=self.text_primary,
            bd=0,
            highlightthickness=0,
            padx=8,
            pady=6,
            wrap="none",
        )
        scrollbar = ttk.Scrollbar(ssid_box_frame, orient=tk.VERTICAL, command=self.txt_ssids.yview)
        self.txt_ssids.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_ssids.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Current Wi-Fi Status Pill
        wifi_pill = tk.Frame(
            card,
            bg=self.badge_bg,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=self.border_color,
            padx=12,
            pady=4,
        )
        wifi_pill.pack(fill=tk.X, pady=(4, 10))

        self.lbl_current_ssid = tk.Label(
            wifi_pill,
            text="Current Wi-Fi: Detecting...",
            font=("Segoe UI", 9),
            fg="#334155",
            bg=self.badge_bg,
        )
        self.lbl_current_ssid.pack(side=tk.LEFT)

        btn_add = ttk.Button(
            wifi_pill,
            text="+ Add to Allowed",
            command=self._add_current_ssid,
            style="Action.TButton",
        )
        btn_add.pack(side=tk.RIGHT)

        btn_clear = ttk.Button(
            wifi_pill,
            text="Clear List",
            command=self._on_clear_ssids,
            style="Action.TButton",
        )
        btn_clear.pack(side=tk.RIGHT, padx=(0, 6))

        # Separator
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # 3. Automation
        ttk.Label(card, text="Automation", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 6))

        self.auto_start_var = tk.BooleanVar(value=True)
        chk_autostart = ttk.Checkbutton(
            card,
            text="Enable auto-login trigger on Wi-Fi connection (Task Scheduler)",
            variable=self.auto_start_var,
            style="TCheckbutton",
        )
        chk_autostart.pack(anchor=tk.W)

        # --- Status Badge Card ---
        status_card = tk.Frame(
            main_container,
            bg=self.card_color,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=self.border_color,
            padx=12,
            pady=8,
        )
        status_card.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(status_card, text="Status:", style="CardLabel.TLabel", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.lbl_status = ttk.Label(
            status_card, text="Ready", style="CardLabel.TLabel", foreground=self.text_secondary
        )
        self.lbl_status.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)

        # --- Bottom Buttons ---
        btn_row = tk.Frame(main_container, bg=self.bg_color)
        btn_row.pack(fill=tk.X)

        self.btn_test = ttk.Button(
            btn_row, text="Test Login Now", command=self._on_test_login, style="Secondary.TButton"
        )
        self.btn_test.pack(side=tk.LEFT)

        self.btn_uninstall = ttk.Button(
            btn_row, text="Uninstall", command=self._on_uninstall, style="Danger.TButton"
        )
        self.btn_uninstall.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_cancel = ttk.Button(
            btn_row, text="Close", command=self.root.destroy, style="Secondary.TButton"
        )
        self.btn_cancel.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_save = ttk.Button(
            btn_row, text="Save & Apply", command=self._on_save, style="Primary.TButton"
        )
        self.btn_save.pack(side=tk.RIGHT)

        # --- Legal & License Disclaimer Footer ---
        footer_frame = tk.Frame(main_container, bg=self.bg_color)
        footer_frame.pack(fill=tk.X, pady=(10, 0))

        lbl_legal = tk.Label(
            footer_frame,
            text="Personal & educational use only • Covered by Open Source License • Selling is prohibited",
            font=("Segoe UI", 7),
            fg="#64748b",
            bg=self.bg_color,
            cursor="hand2",
        )
        lbl_legal.pack(side=tk.LEFT)
        lbl_legal.bind("<Button-1>", lambda e: self._show_license_dialog())

        btn_about = tk.Label(
            footer_frame,
            text="[License & Terms]",
            font=("Segoe UI", 7, "underline"),
            fg="#2563eb",
            bg=self.bg_color,
            cursor="hand2",
        )
        btn_about.pack(side=tk.RIGHT)
        btn_about.bind("<Button-1>", lambda e: self._show_license_dialog())

    def _show_license_dialog(self):
        messagebox.showinfo(
            "License, Terms & Legal Disclaimer",
            "CAMPUS WI-FI AUTO-LOGIN — OPEN SOURCE UTILITY\n"
            "==============================================\n\n"
            "• LICENSE: Free for personal and educational use only under the Open Source License.\n\n"
            "• COMMERCIAL SALE PROHIBITED: Selling, re-selling, paid redistribution, or commercial monetization of this software is strictly prohibited.\n\n"
            "• NO AFFILIATION: This independent student utility is NOT affiliated with, sponsored by, or endorsed by any university, educational institution, or firewall vendor (e.g. Palo Alto Networks).\n\n"
            "• DISCLAIMER OF LIABILITY: Provided 'AS IS' without warranty of any kind. Users are responsible for complying with their institution's Acceptable Use Policies and using only their own valid credentials.",
            parent=self.root,
        )

    def _toggle_password(self):
        if self.show_pass_var.get():
            self.entry_password.config(show="")
        else:
            self.entry_password.config(show="•")

    def _load_current_values(self):
        cfg = load_config()
        user, pwd = get_credentials()

        if user:
            self.entry_username.insert(0, user)
        if pwd:
            self.entry_password.insert(0, pwd)

        self.entry_host.insert(0, cfg.get("portal_host", "192.168.100.1:6082"))

        ssids = cfg.get("allowed_ssids", [])
        self.txt_ssids.delete("1.0", tk.END)
        self.txt_ssids.insert(tk.END, "\n".join(ssids))

        self.auto_start_var.set(is_task_registered())

        threading.Thread(target=self._refresh_ssid_label, daemon=True).start()

    def _refresh_ssid_label(self):
        curr = get_current_ssid()
        if curr:
            self.lbl_current_ssid.config(text=f"Current Wi-Fi: {curr}")
            self.current_detected_ssid = curr
        else:
            self.lbl_current_ssid.config(text="Current Wi-Fi: Not connected")
            self.current_detected_ssid = None

    def _get_parsed_ssids(self):
        """Parse allowed SSIDs supporting newlines, commas, and multi-entry lines."""
        raw_text = self.txt_ssids.get("1.0", tk.END)
        ssids = []
        for line in raw_text.splitlines():
            tokens = [t.strip() for t in line.split(",") if t.strip()]
            for token in tokens:
                if token and token not in ssids:
                    ssids.append(token)
        return ssids

    def _add_current_ssid(self):
        if hasattr(self, "current_detected_ssid") and self.current_detected_ssid:
            ssids = self._get_parsed_ssids()
            if self.current_detected_ssid not in ssids:
                ssids.append(self.current_detected_ssid)
                self.txt_ssids.delete("1.0", tk.END)
                self.txt_ssids.insert(tk.END, "\n".join(ssids))
                self._set_status(f"Added '{self.current_detected_ssid}' to list", color="#16a34a")
            else:
                self._set_status(f"'{self.current_detected_ssid}' is already in list", color="#64748b")
        else:
            messagebox.showinfo("Wi-Fi Status", "No active Wi-Fi interface detected currently.")

    def _set_status(self, text, color=None):
        self.lbl_status.config(text=text, foreground=color or self.text_secondary)

    def _on_save(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get()
        host = self.entry_host.get().strip()
        ssids = self._get_parsed_ssids()

        if not username:
            messagebox.showerror("Validation Error", "Username cannot be empty.")
            return

        if not password:
            messagebox.showerror("Validation Error", "Password cannot be empty.")
            return

        if not host:
            messagebox.showerror("Validation Error", "Portal host cannot be empty.")
            return

        save_credentials(username, password)

        save_config({
            "portal_host": host,
            "allowed_ssids": ssids,
        })

        if self.auto_start_var.get():
            ok, msg = register_task()
            if not ok:
                messagebox.showwarning(
                    "Task Scheduler", f"Settings saved, but automatic task registration returned: {msg}"
                )
        else:
            unregister_task()

        self._set_status("Settings saved successfully!", color="#16a34a")
        messagebox.showinfo("Success", "Configuration and credentials saved successfully.")
        self.root.destroy()

    def _on_test_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get()
        host = self.entry_host.get().strip()
        ssids = self._get_parsed_ssids()

        if not username or not password:
            messagebox.showerror("Validation Error", "Please enter username and password before testing.")
            return

        save_credentials(username, password)
        save_config({
            "portal_host": host,
            "allowed_ssids": ssids,
        })

        self.btn_test.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)
        self._set_status("Testing captive portal connection...", color=self.primary_blue)

        def worker():
            success = execute_auto_login(ignore_ssid=True)
            self.root.after(0, lambda: self._test_finished(success))

        threading.Thread(target=worker, daemon=True).start()

    def _test_finished(self, result):
        self.btn_test.config(state=tk.NORMAL)
        self.btn_save.config(state=tk.NORMAL)
        if result is True:
            self._set_status("Online verified! Login successful.", color="#16a34a")
            messagebox.showinfo("Login Test", "Connection verified successfully! You are online.", parent=self.root)
        elif result == "AUTH_FAILED":
            self._set_status("Authentication failed: Invalid username or password.", color="#dc2626")
            messagebox.showerror(
                "Authentication Failed",
                "The captive portal rejected your username or password.\n\nPlease check your credentials and try again.",
                parent=self.root,
            )
        else:
            self._set_status("Authentication attempt failed or already online.", color="#dc2626")
            messagebox.showwarning(
                "Login Test",
                "Authentication test did not complete. Either you are already authenticated, not connected to portal Wi-Fi, or network timed out.",
                parent=self.root,
            )

    def _on_clear_ssids(self):
        self.txt_ssids.delete("1.0", tk.END)
        self._set_status("Allowed SSIDs list cleared", color="#64748b")

    def _on_uninstall(self):
        confirmed = messagebox.askyesno(
            "Confirm Uninstallation",
            "Are you sure you want to uninstall Campus Wi-Fi Auto-Login?\n\n"
            "This action will:\n"
            "• Remove automatic background Wi-Fi event triggers\n"
            "• Erase all stored credentials from Windows Credential Locker\n"
            "• Delete all saved network configuration and local settings\n\n"
            "Do you want to proceed?",
            icon="warning",
            parent=self.root,
        )
        if not confirmed:
            return

        # 1. Unregister background trigger
        unregister_task()

        # 2. Wipe all credentials and local data
        clear_all_data()

        # 3. If running from an Inno Setup installation, trigger official uninstaller
        app_dir = Path(__file__).resolve().parent
        unins = app_dir / "unins000.exe"
        if not unins.exists():
            local_app = os.environ.get("LOCALAPPDATA")
            if local_app:
                cand = Path(local_app) / "Programs" / "CampusWifiLogin" / "unins000.exe"
                if cand.exists():
                    unins = cand

        if unins.exists():
            try:
                import subprocess
                self.root.destroy()
                subprocess.Popen([str(unins)])
                return
            except Exception:
                pass

        messagebox.showinfo(
            "Uninstallation Complete",
            "Background automation removed and all login credentials successfully erased.",
            parent=self.root,
        )
        self.root.destroy()


def launch_gui(prompt_reauth=False):
    root = tk.Tk()
    app = CampusLoginApp(root, prompt_reauth=prompt_reauth)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
