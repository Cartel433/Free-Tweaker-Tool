
import customtkinter as ctk
import threading
import subprocess
import json
import ctypes
import sys
import os
from pathlib import Path
from datetime import datetime

#Theme 
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = Path.home() / ".nzsv_optimizer.json"

#Colour palette 
C_BG        = "#080C10"   # near-black base
C_PANEL     = "#0D1117"   # sidebar / panel
C_CARD      = "#111820"   # card surface
C_CARD2     = "#0A0F14"   # inset / textbox bg
C_BORDER    = "#1C2A38"   # subtle border
C_CYAN      = "#00E5FF"   # electric cyan primary
C_CYAN_DIM  = "#007A8A"   # dimmed cyan
C_CYAN_GLOW = "#00BFCC"   # hover cyan
C_RED       = "#FF3B3B"   # danger
C_ORANGE    = "#FF8C00"   # warning
C_GREEN     = "#00FF88"   # success
C_WHITE     = "#E8EDF2"   # primary text
C_MUTED     = "#4A6070"   # muted text
C_MONO      = "Consolas"  # monospace font
C_SANS      = "Segoe UI"  # UI font


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def run_cmd(cmd, shell=False):
    """Run a command, return (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True,
            timeout=60, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), -1


def reg_add(path, name, type_, value):
    """Add a registry value. Returns True on success."""
    out, err, code = run_cmd(
        ["reg", "add", path, "/v", name, "/t", type_, "/d", str(value), "/f"]
    )
    return code == 0


def sc_config(service, start):
    """Configure a service startup type."""
    run_cmd(["sc", "config", service, f"start={start}"])


def sc_stop(service):
    run_cmd(["sc", "stop", service])


# Name Setup Window
class NameSetupWindow(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("NZSV — First Launch")
        self.geometry("500x360")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self.grab_set()
        self.lift()

        #Top accent bar
        ctk.CTkFrame(self, height=3, fg_color=C_CYAN, corner_radius=0).pack(fill="x")

        ctk.CTkLabel(
            self, text="NZSV",
            font=ctk.CTkFont(family=C_MONO, size=42, weight="bold"),
            text_color=C_CYAN
        ).pack(pady=(36, 0))

        ctk.CTkLabel(
            self, text="WIN OPTIMIZER PRO",
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=C_MUTED
        ).pack()

        ctk.CTkFrame(self, height=1, fg_color=C_BORDER).pack(fill="x", padx=40, pady=22)

        ctk.CTkLabel(
            self, text="Enter your name to personalise your session",
            font=ctk.CTkFont(family=C_SANS, size=13),
            text_color=C_MUTED
        ).pack()

        self.name_entry = ctk.CTkEntry(
            self,
            placeholder_text="Your name...",
            width=300, height=46,
            font=ctk.CTkFont(family=C_MONO, size=14),
            corner_radius=4,
            fg_color=C_CARD,
            border_color=C_CYAN,
            text_color=C_WHITE
        )
        self.name_entry.pack(pady=16)
        self.name_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            self,
            text="INITIALISE  ▶",
            command=self._submit,
            width=300, height=44,
            corner_radius=4,
            fg_color=C_CYAN,
            hover_color=C_CYAN_GLOW,
            text_color=C_BG,
            font=ctk.CTkFont(family=C_MONO, size=13, weight="bold")
        ).pack()

        self.err_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=C_RED
        )
        self.err_label.pack(pady=6)

    def _submit(self):
        name = self.name_entry.get().strip()
        if not name:
            self.err_label.configure(text="[ ERROR ] Name cannot be empty.")
            return
        self.destroy()
        self.callback(name)


#Main App
class NZSVOptimizer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.user_name   = self.config_data.get("name", "")

        self.title("NZSV WinOptimizer Pro")
        self.geometry("1100x720")
        self.minsize(960, 640)
        self.configure(fg_color=C_BG)

        if not self.user_name:
            self.withdraw()
            self.after(100, self._ask_name)
        else:
            self._build_ui()

    def _ask_name(self):
        NameSetupWindow(self, self._on_name_set)

    def _on_name_set(self, name):
        self.user_name = name
        self.config_data["name"] = name
        save_config(self.config_data)
        self.deiconify()
        self._build_ui()

    # UI Shell
    def _build_ui(self):
        # Top bar
        topbar = ctk.CTkFrame(self, height=46, fg_color=C_PANEL, corner_radius=0)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        ctk.CTkFrame(topbar, width=3, fg_color=C_CYAN, corner_radius=0).pack(
            side="left", fill="y"
        )
        ctk.CTkLabel(
            topbar, text="  NZSV  WIN OPTIMIZER PRO",
            font=ctk.CTkFont(family=C_MONO, size=13, weight="bold"),
            text_color=C_CYAN
        ).pack(side="left", padx=14)

        # Admin badge
        a_col  = C_GREEN if is_admin() else C_ORANGE
        a_text = "▲ ADMIN" if is_admin() else "▼ LIMITED"
        ctk.CTkLabel(
            topbar, text=a_text,
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=a_col
        ).pack(side="right", padx=18)

        ctk.CTkLabel(
            topbar,
            text=f"  USER: {self.user_name.upper()}",
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=C_MUTED
        ).pack(side="right")

        #
        ctk.CTkFrame(self, height=1, fg_color=C_CYAN, corner_radius=0).pack(fill="x")

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_content(body)

    def _build_sidebar(self, parent):
        sb = ctk.CTkFrame(parent, width=210, fg_color=C_PANEL, corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        ctk.CTkFrame(sb, height=1, fg_color=C_BORDER).pack(fill="x", pady=(0, 10))

        nav_items = [
            ("⬡  DASHBOARD",   "dashboard"),
            ("◈  LOW LATENCY", "lowlatency"),
            ("◉  TWEAKS",      "tweaks"),
            ("⬢  CLEANER",     "cleaner"),
            ("◎  NETWORK",     "network"),
            ("⚙  SETTINGS",   "settings"),
        ]

        self.nav_btns = {}
        for label, key in nav_items:
            btn = ctk.CTkButton(
                sb, text=label,
                anchor="w",
                width=194, height=38,
                corner_radius=0,
                fg_color="transparent",
                hover_color="#0A1A26",
                text_color=C_MUTED,
                font=ctk.CTkFont(family=C_MONO, size=12),
                command=lambda k=key: self._switch(k)
            )
            btn.pack(padx=0, pady=1)
            self.nav_btns[key] = btn

        # Bottom decorative box
        ctk.CTkFrame(sb, height=1, fg_color=C_BORDER).pack(
            fill="x", side="bottom", pady=10
        )
        ctk.CTkLabel(
            sb,
            text=f"  {self.user_name}\n  NZSV v2.0",
            font=ctk.CTkFont(family=C_MONO, size=10),
            text_color=C_MUTED,
            justify="left"
        ).pack(side="bottom", anchor="w", padx=16, pady=6)

    def _build_content(self, parent):
        self.content_area = ctk.CTkFrame(parent, fg_color=C_BG, corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.pages = {}
        self._page_dashboard()
        self._page_lowlatency()
        self._page_tweaks()
        self._page_cleaner()
        self._page_network()
        self._page_settings()

        self._switch("dashboard")

    def _switch(self, key):
        for frame in self.pages.values():
            frame.pack_forget()
        for k, btn in self.nav_btns.items():
            btn.configure(
                fg_color="transparent" if k != key else C_CARD,
                text_color=C_MUTED if k != key else C_CYAN,
                border_width=0 if k != key else 0
            )
        self.pages[key].pack(fill="both", expand=True)

    # Widget Helpers
    def _page_frame(self, key):
        f = ctk.CTkScrollableFrame(
            self.content_area, fg_color="transparent", corner_radius=0
        )
        self.pages[key] = f
        return f

    def _card(self, parent, **kw):
        return ctk.CTkFrame(
            parent, fg_color=C_CARD, corner_radius=6,
            border_width=1, border_color=C_BORDER, **kw
        )

    def _heading(self, parent, text, sub=""):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(family=C_MONO, size=20, weight="bold"),
            text_color=C_CYAN
        ).pack(anchor="w", pady=(0, 2))
        if sub:
            ctk.CTkLabel(
                parent, text=sub,
                font=ctk.CTkFont(family=C_SANS, size=12),
                text_color=C_MUTED
            ).pack(anchor="w", pady=(0, 16))

    def _cyan_btn(self, parent, text, cmd, w=160, h=38):
        return ctk.CTkButton(
            parent, text=text, command=cmd,
            width=w, height=h, corner_radius=4,
            fg_color=C_CYAN, hover_color=C_CYAN_GLOW,
            text_color=C_BG,
            font=ctk.CTkFont(family=C_MONO, size=12, weight="bold")
        )

    def _ghost_btn(self, parent, text, cmd, w=160, h=38):
        return ctk.CTkButton(
            parent, text=text, command=cmd,
            width=w, height=h, corner_radius=4,
            fg_color="transparent", hover_color=C_CARD2,
            text_color=C_CYAN, border_width=1, border_color=C_CYAN_DIM,
            font=ctk.CTkFont(family=C_MONO, size=12)
        )

    def _log_box(self, parent, height=160):
        box = ctk.CTkTextbox(
            parent,
            height=height,
            fg_color=C_CARD2,
            corner_radius=4,
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=C_GREEN,
            border_width=1,
            border_color=C_BORDER
        )
        box.configure(state="disabled")
        return box

    def _log(self, box, msg, color=None):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        try:
            box.configure(state="normal")
            box.insert("end", line)
            box.see("end")
            box.configure(state="disabled")
        except Exception:
            pass
        # 
        if box is not getattr(self, "_global_log", None):
            try:
                self._log(self._global_log, msg)
            except Exception:
                pass

    def _set_box(self, box, text):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.configure(state="disabled")

    def _progress_row(self, parent):
        bar = ctk.CTkProgressBar(
            parent, height=4, corner_radius=2,
            fg_color=C_BORDER, progress_color=C_CYAN
        )
        bar.set(0)
        bar.pack(fill="x", pady=(8, 0))
        return bar

    def _status_label(self, parent):
        lbl = ctk.CTkLabel(
            parent, text="",
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=C_MUTED
        )
        lbl.pack(anchor="w", pady=2)
        return lbl

    # 
    # PAGES
    # 

    # Dashboard 
    def _page_dashboard(self):
        f = self._page_frame("dashboard")
        pad = {"padx": 28, "pady": (24, 0)}

        # Header
        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.pack(fill="x", **pad)
        self._heading(
            hdr,
            f"WELCOME BACK, {self.user_name.upper()}",
            "System optimisation suite — NZSV edition"
        )

        # Stat cards
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=10)

        stats = [
            ("⬡", "LOW LATENCY 1",  "Full system perf tweaks",  C_CYAN),
            ("◈", "LOW LATENCY 2",  "Registry & GPU boosts",    C_CYAN),
            ("◉", "TWEAKS PACK 1",  "Animations & boot speed",  C_CYAN),
            ("⬢", "TWEAKS PACK 2",  "Deep system optimisation", C_CYAN),
        ]
        for icon, title, desc, col in stats:
            c = self._card(row)
            c.pack(side="left", fill="both", expand=True, padx=(0, 10))
            ctk.CTkLabel(c, text=icon, font=ctk.CTkFont(family=C_MONO, size=24),
                         text_color=col).pack(anchor="w", padx=16, pady=(16, 4))
            ctk.CTkLabel(c, text=title,
                         font=ctk.CTkFont(family=C_MONO, size=12, weight="bold"),
                         text_color=C_WHITE).pack(anchor="w", padx=16)
            ctk.CTkLabel(c, text=desc,
                         font=ctk.CTkFont(family=C_SANS, size=11),
                         text_color=C_MUTED).pack(anchor="w", padx=16, pady=(2, 14))

        # Quick run row
        qc = self._card(f)
        qc.pack(fill="x", padx=28, pady=10)
        ctk.CTkLabel(qc, text="QUICK ACTIONS",
                     font=ctk.CTkFont(family=C_MONO, size=11),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(12, 6))
        brow = ctk.CTkFrame(qc, fg_color="transparent")
        brow.pack(fill="x", padx=16, pady=(0, 14))

        self._cyan_btn(brow, "▶ RUN ALL TWEAKS", self._run_all_tweaks).pack(
            side="left", padx=(0, 10)
        )
        self._ghost_btn(brow, "⬢ CLEAN JUNK", lambda: self._switch("cleaner")).pack(
            side="left", padx=(0, 10)
        )
        self._ghost_btn(brow, "◎ FLUSH DNS", self._quick_flush_dns).pack(side="left")

        # Global log
        lc = self._card(f)
        lc.pack(fill="x", padx=28, pady=10)
        ctk.CTkLabel(lc, text="ACTIVITY LOG",
                     font=ctk.CTkFont(family=C_MONO, size=11),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(12, 4))
        self._global_log = self._log_box(lc, height=180)
        self._global_log.pack(fill="x", padx=14, pady=(0, 14))

        self._log(self._global_log,
                  f"NZSV WinOptimizer Pro initialised — user: {self.user_name}")
        if not is_admin():
            self._log(self._global_log,
                      "WARNING: Not running as Administrator. Some tweaks will fail.")

    def _run_all_tweaks(self):
        threading.Thread(target=self._do_all_tweaks, daemon=True).start()

    def _do_all_tweaks(self):
        self._log(self._global_log, "=== RUNNING ALL TWEAK PACKS ===")
        self._apply_ll1_tweaks(self._global_log, lambda v: None)
        self._apply_ll2_tweaks(self._global_log, lambda v: None)
        self._apply_tweaks3(self._global_log, lambda v: None)
        self._apply_tweaks4(self._global_log, lambda v: None)
        self._log(self._global_log, "=== ALL TWEAKS COMPLETE — RESTART RECOMMENDED ===")

    def _quick_flush_dns(self):
        def run():
            run_cmd(["ipconfig", "/flushdns"])
            self._log(self._global_log, "DNS cache flushed.")
        threading.Thread(target=run, daemon=True).start()

    # Low Latency Page
    def _page_lowlatency(self):
        f = self._page_frame("lowlatency")
        pad = {"padx": 28, "pady": (24, 0)}

        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.pack(fill="x", **pad)
        self._heading(hdr, "LOW LATENCY PACKS",
                      "Performance registry tweaks, GPU tuning, MMCSS & kernel optimisations")

        # Pack 1
        c1 = self._card(f)
        c1.pack(fill="x", padx=28, pady=8)
        self._pack_header(c1, "LOW LATENCY PACK 1", [
            "High Performance power plan",
            "Disable SysMain / BITS / print spooler",
            "Foreground app priority boost",
            "Flush DNS",
            "Disable Windows Tips & Cortana",
            "Large System Cache enabled",
            "Network tuning (TCP autotune off)",
            "Disable Windows Search indexing",
            "Pagefile set to 8192–16384 MB",
            "Disable automatic updates",
            "Disable visual effects",
        ])
        btn_row1 = ctk.CTkFrame(c1, fg_color="transparent")
        btn_row1.pack(fill="x", padx=16, pady=(0, 6))
        self.ll1_prog = self._progress_row(c1)
        self.ll1_status = self._status_label(c1)
        self.ll1_log = self._log_box(c1, height=140)
        self.ll1_log.pack(fill="x", padx=14, pady=(4, 14))
        self._cyan_btn(btn_row1, "▶ APPLY PACK 1",
                       lambda: threading.Thread(
                           target=self._apply_ll1_tweaks,
                           args=(self.ll1_log, self.ll1_prog.set),
                           daemon=True
                       ).start()
                       ).pack(side="left")

        #  Pack 2 
        c2 = self._card(f)
        c2.pack(fill="x", padx=28, pady=8)
        self._pack_header(c2, "LOW LATENCY PACK 2", [
            "MMCSS Games profile — GPU Priority 8 / CPU Priority 6",
            "Disable Power Throttling",
            "Disable GameDVR / Xbox DVR overlay",
            "Hardware GPU Scheduling (HAGS) enabled",
            "Disable VRR (Variable Refresh Rate)",
            "Disable hibernation & Hiberboot",
            "Kernel kill-timeout tweaks (HungApp, WaitToKill)",
            "Disable auto-maintenance",
            "No-lock-screen policy",
            "Disable telemetry & DiagTrack",
            "Disable Xbox Live services",
            "Disable Bluetooth services (Audio Gateway, Support)",
            "Mouse acceleration OFF (MouseThreshold 0)",
            "Disable Ease of Access shortcuts",
            "Privacy: advertising ID, location, app diagnostics off",
            "AMD GPU power gating & stutter mode tweaks",
            "Win32PrioritySeparation set to optimal",
        ])
        btn_row2 = ctk.CTkFrame(c2, fg_color="transparent")
        btn_row2.pack(fill="x", padx=16, pady=(0, 6))
        self.ll2_prog = self._progress_row(c2)
        self.ll2_status = self._status_label(c2)
        self.ll2_log = self._log_box(c2, height=140)
        self.ll2_log.pack(fill="x", padx=14, pady=(4, 14))
        self._cyan_btn(btn_row2, "▶ APPLY PACK 2",
                       lambda: threading.Thread(
                           target=self._apply_ll2_tweaks,
                           args=(self.ll2_log, self.ll2_prog.set),
                           daemon=True
                       ).start()
                       ).pack(side="left")

    # Tweaks Page
    def _page_tweaks(self):
        f = self._page_frame("tweaks")
        pad = {"padx": 28, "pady": (24, 0)}

        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.pack(fill="x", **pad)
        self._heading(hdr, "SYSTEM TWEAKS",
                      "Boot speed, animation removal, privacy hardening & deep optimisation")

        # Tweaks 3
        c3 = self._card(f)
        c3.pack(fill="x", padx=28, pady=8)
        self._pack_header(c3, "TWEAKS PACK 1 — BOOT & ANIMATIONS", [
            "Disable all window animations",
            "Remove lock screen",
            "Disable startup delay (StartupDelayInMSec = 0)",
            "Enable fast startup / hibernate on",
            "Disable standby & display timeout (AC + DC)",
        ])
        btn_row3 = ctk.CTkFrame(c3, fg_color="transparent")
        btn_row3.pack(fill="x", padx=16, pady=(0, 6))
        self.t3_prog = self._progress_row(c3)
        self.t3_status = self._status_label(c3)
        self.t3_log = self._log_box(c3, height=120)
        self.t3_log.pack(fill="x", padx=14, pady=(4, 14))
        self._cyan_btn(btn_row3, "▶ APPLY PACK 1",
                       lambda: threading.Thread(
                           target=self._apply_tweaks3,
                           args=(self.t3_log, self.t3_prog.set),
                           daemon=True
                       ).start()
                       ).pack(side="left")

        # Tweaks 4
        c4 = self._card(f)
        c4.pack(fill="x", padx=28, pady=8)
        self._pack_header(c4, "TWEAKS PACK 2 — DEEP SYSTEM OPTIMISATION", [
            "Clean temp / prefetch files",
            "Disable OneDrive & Skype from startup",
            "Visual effects → best performance",
            "High Performance power plan",
            "Disable SysMain, DiagTrack, dmwappushservice",
            "Disable hibernation to free disk space",
            "Clear DNS cache",
            "Disable Windows Tips & notifications",
            "Disable remote assistance",
            "Menu show delay → 20ms",
            "Disable background apps globally",
            "Disable Cortana",
            "Disable telemetry (AllowTelemetry = 0)",
            "Disable Windows Error Reporting",
            "Speed up shutdown (WaitToKillService = 5000ms)",
            "Disable indexer backoff",
            "Disable automatic driver updates",
        ])
        btn_row4 = ctk.CTkFrame(c4, fg_color="transparent")
        btn_row4.pack(fill="x", padx=16, pady=(0, 6))
        self.t4_prog = self._progress_row(c4)
        self.t4_status = self._status_label(c4)
        self.t4_log = self._log_box(c4, height=120)
        self.t4_log.pack(fill="x", padx=14, pady=(4, 14))
        self._cyan_btn(btn_row4, "▶ APPLY PACK 2",
                       lambda: threading.Thread(
                           target=self._apply_tweaks4,
                           args=(self.t4_log, self.t4_prog.set),
                           daemon=True
                       ).start()
                       ).pack(side="left")

    def _pack_header(self, parent, title, bullets):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(family=C_MONO, size=13, weight="bold"),
            text_color=C_CYAN
        ).pack(anchor="w", padx=16, pady=(14, 6))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 10))
        for i, b in enumerate(bullets):
            col = i % 2
            row = i // 2
            ctk.CTkLabel(
                grid,
                text=f"  ▸ {b}",
                font=ctk.CTkFont(family=C_SANS, size=11),
                text_color=C_MUTED,
                anchor="w"
            ).grid(row=row, column=col, sticky="w", padx=(0, 30), pady=1)

    # Cleaner Page
    def _page_cleaner(self):
        f = self._page_frame("cleaner")
        pad = {"padx": 28, "pady": (24, 0)}

        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.pack(fill="x", **pad)
        self._heading(hdr, "SYSTEM CLEANER",
                      f"Junk removal for {self.user_name}'s machine")

        # Checkboxes
        opt_card = self._card(f)
        opt_card.pack(fill="x", padx=28, pady=8)
        ctk.CTkLabel(opt_card, text="SELECT TARGETS",
                     font=ctk.CTkFont(family=C_MONO, size=11),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(12, 6))

        self.clean_opts = {}
        opts = [
            ("Temp Files",            True),
            ("Windows Temp",          True),
            ("Prefetch Files",        True),
            ("Recycle Bin",           True),
            ("DNS Cache",             True),
            ("Windows Store Cache",   False),
        ]
        g = ctk.CTkFrame(opt_card, fg_color="transparent")
        g.pack(fill="x", padx=16, pady=(0, 14))
        for i, (name, default) in enumerate(opts):
            var = ctk.BooleanVar(value=default)
            self.clean_opts[name] = var
            ctk.CTkCheckBox(
                g, text=name, variable=var,
                font=ctk.CTkFont(family=C_MONO, size=12),
                text_color=C_WHITE,
                checkmark_color=C_BG,
                fg_color=C_CYAN,
                hover_color=C_CYAN_GLOW,
                border_color=C_BORDER
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 40), pady=4)

        # Buttons
        br = ctk.CTkFrame(f, fg_color="transparent")
        br.pack(fill="x", padx=28, pady=6)
        self._cyan_btn(br, "▶ CLEAN NOW", self._run_clean).pack(side="left", padx=(0, 10))
        self._ghost_btn(br, "⟳ SCAN FIRST", self._scan_junk).pack(side="left")

        self.clean_prog = self._progress_row(f)
        self.clean_prog.pack(fill="x", padx=28)

        res_card = self._card(f)
        res_card.pack(fill="x", padx=28, pady=8)
        ctk.CTkLabel(res_card, text="OUTPUT",
                     font=ctk.CTkFont(family=C_MONO, size=11),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(12, 4))
        self.clean_log = self._log_box(res_card, height=180)
        self.clean_log.pack(fill="x", padx=14, pady=(0, 14))

    def _scan_junk(self):
        def run():
            import tempfile
            temp = Path(tempfile.gettempdir())
            size = sum(
                f.stat().st_size for f in temp.rglob("*") if f.is_file()
            ) if temp.exists() else 0
            mb = size / (1024 * 1024)
            self._log(self.clean_log, f"SCAN: ~{mb:.1f} MB in %TEMP%")
            pf = Path("C:/Windows/Prefetch")
            pf_count = len(list(pf.glob("*.pf"))) if pf.exists() else 0
            self._log(self.clean_log, f"SCAN: {pf_count} prefetch files")
            self._log(self.clean_log, "Scan complete. Run CLEAN NOW to proceed.")
        threading.Thread(target=run, daemon=True).start()

    def _run_clean(self):
        selected = [k for k, v in self.clean_opts.items() if v.get()]
        if not selected:
            self._log(self.clean_log, "ERROR: No targets selected.")
            return
        threading.Thread(target=self._do_clean, args=(selected,), daemon=True).start()

    def _do_clean(self, selected):
        total = len(selected)
        for i, task in enumerate(selected):
            self.after(0, lambda v=(i + 1) / total: self.clean_prog.set(v))
            try:
                if task == "Temp Files":
                    import tempfile, shutil
                    count = 0
                    for item in Path(tempfile.gettempdir()).iterdir():
                        try:
                            if item.is_file(): item.unlink(); count += 1
                            elif item.is_dir(): shutil.rmtree(item, ignore_errors=True); count += 1
                        except: pass
                    self._log(self.clean_log, f"Temp Files: {count} items removed")

                elif task == "Windows Temp":
                    import shutil
                    wt = Path("C:/Windows/Temp")
                    count = 0
                    if wt.exists():
                        for item in wt.iterdir():
                            try:
                                if item.is_file(): item.unlink(); count += 1
                                elif item.is_dir(): shutil.rmtree(item, ignore_errors=True); count += 1
                            except: pass
                    self._log(self.clean_log, f"Windows Temp: {count} items removed")

                elif task == "Prefetch Files":
                    pf = Path("C:/Windows/Prefetch")
                    count = 0
                    if pf.exists():
                        for item in pf.glob("*.pf"):
                            try: item.unlink(); count += 1
                            except: pass
                    self._log(self.clean_log, f"Prefetch: {count} files removed")

                elif task == "Recycle Bin":
                    run_cmd(["powershell", "-Command",
                             "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"])
                    self._log(self.clean_log, "Recycle Bin: Emptied")

                elif task == "DNS Cache":
                    run_cmd(["ipconfig", "/flushdns"])
                    self._log(self.clean_log, "DNS Cache: Flushed")

                elif task == "Windows Store Cache":
                    run_cmd(["wsreset.exe"])
                    self._log(self.clean_log, "Windows Store Cache: Reset triggered")

            except Exception as e:
                self._log(self.clean_log, f"{task}: ERROR — {e}")

        self._log(self.clean_log, "=== CLEAN COMPLETE ===")

    # Network Page
    def _page_network(self):
        f = self._page_frame("network")
        pad = {"padx": 28, "pady": (24, 0)}

        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.pack(fill="x", **pad)
        self._heading(hdr, "NETWORK TOOLS", "Connectivity diagnostics and tuning")

        tools = [
            ("FLUSH DNS",      "Clear resolver cache",            self._net_flush_dns),
            ("RESET WINSOCK",  "Reset Windows network stack",     self._net_winsock),
            ("IP CONFIG",      "Show all adapter information",    self._net_ipconfig),
            ("PING 8.8.8.8",   "Test internet connectivity",      self._net_ping),
            ("TCP TUNING",     "Apply low-latency TCP settings",  self._net_tcp_tune),
        ]

        for label, desc, cmd in tools:
            tc = self._card(f)
            tc.pack(fill="x", padx=28, pady=5)
            row = ctk.CTkFrame(tc, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=12)
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(family=C_MONO, size=12, weight="bold"),
                         text_color=C_WHITE).pack(side="left")
            ctk.CTkLabel(row, text=f"  —  {desc}",
                         font=ctk.CTkFont(family=C_SANS, size=11),
                         text_color=C_MUTED).pack(side="left")
            self._cyan_btn(row, "RUN", cmd, w=90, h=32).pack(side="right")

        out_card = self._card(f)
        out_card.pack(fill="x", padx=28, pady=10)
        ctk.CTkLabel(out_card, text="OUTPUT",
                     font=ctk.CTkFont(family=C_MONO, size=11),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(12, 4))
        self.net_log = self._log_box(out_card, height=200)
        self.net_log.pack(fill="x", padx=14, pady=(0, 14))

    def _net_flush_dns(self):
        def run():
            out, _, _ = run_cmd(["ipconfig", "/flushdns"])
            self._log(self.net_log, out or "DNS flushed.")
        threading.Thread(target=run, daemon=True).start()

    def _net_winsock(self):
        def run():
            out, _, _ = run_cmd(["netsh", "winsock", "reset"])
            self._log(self.net_log, out or "Winsock reset. Restart required.")
        threading.Thread(target=run, daemon=True).start()

    def _net_ipconfig(self):
        def run():
            out, _, _ = run_cmd(["ipconfig", "/all"])
            self._set_box(self.net_log, out)
        threading.Thread(target=run, daemon=True).start()

    def _net_ping(self):
        def run():
            out, _, _ = run_cmd(["ping", "-n", "4", "8.8.8.8"])
            self._set_box(self.net_log, out)
        threading.Thread(target=run, daemon=True).start()

    def _net_tcp_tune(self):
        def run():
            cmds = [
                ["netsh", "int", "tcp", "set", "global", "autotuninglevel=disabled"],
                ["netsh", "int", "tcp", "set", "global", "rsc=disabled"],
                ["netsh", "int", "tcp", "set", "global", "chimney=disabled"],
            ]
            for c in cmds:
                out, err, code = run_cmd(c)
                self._log(self.net_log, f"{' '.join(c[4:])}: {'OK' if code == 0 else err}")
        threading.Thread(target=run, daemon=True).start()

    # Settings Page
    def _page_settings(self):
        f = self._page_frame("settings")
        pad = {"padx": 28, "pady": (24, 0)}

        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.pack(fill="x", **pad)
        self._heading(hdr, "SETTINGS", "Preferences and app configuration")

        nc = self._card(f)
        nc.pack(fill="x", padx=28, pady=8)
        ctk.CTkLabel(nc, text="DISPLAY NAME",
                     font=ctk.CTkFont(family=C_MONO, size=11),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(14, 4))

        nr = ctk.CTkFrame(nc, fg_color="transparent")
        nr.pack(fill="x", padx=16, pady=(0, 14))
        self.sett_name = ctk.CTkEntry(
            nr, width=280, height=40,
            font=ctk.CTkFont(family=C_MONO, size=13),
            fg_color=C_CARD2, border_color=C_CYAN,
            text_color=C_WHITE, corner_radius=4
        )
        self.sett_name.insert(0, self.user_name)
        self.sett_name.pack(side="left")
        self._cyan_btn(nr, "SAVE", self._save_name, w=100, h=40).pack(
            side="left", padx=10
        )
        self.sett_msg = ctk.CTkLabel(
            nr, text="",
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=C_GREEN
        )
        self.sett_msg.pack(side="left")

        # About
        ac = self._card(f)
        ac.pack(fill="x", padx=28, pady=8)
        ctk.CTkLabel(ac, text="ABOUT",
                     font=ctk.CTkFont(family=C_MONO, size=11),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            ac,
            text="NZSV WinOptimizer Pro  v2.0\n"
                 "Built with Python + CustomTkinter\n"
                 "Integrates: Low Latency 1 & 2, Tweaks Pack 1 & 2\n"
                 "Compatible: Windows 10 / 11  |  Run as Administrator for full access",
            font=ctk.CTkFont(family=C_MONO, size=11),
            text_color=C_MUTED,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _save_name(self):
        name = self.sett_name.get().strip()
        if not name:
            return
        self.user_name = name
        self.config_data["name"] = name
        save_config(self.config_data)
        self.sett_msg.configure(text="  ✔ SAVED")
        self._log(self._global_log, f"Name updated → {name}")
        self.after(2500, lambda: self.sett_msg.configure(text=""))

    # 
    # TWEAK IMPLEMENTATIONS
    #

    # Low Latency 1
    def _apply_ll1_tweaks(self, log, set_prog):
        tasks = [
            ("High Performance power plan",
             lambda: run_cmd(["powercfg", "/setactive", "SCHEME_MIN"])),

            ("Disable SysMain (Superfetch)",
             lambda: (sc_stop("SysMain"), sc_config("SysMain", "disabled"))),

            ("Disable BITS",
             lambda: (sc_stop("BITS"), sc_config("BITS", "disabled"))),

            ("Disable Print Spooler",
             lambda: (sc_stop("Spooler"), sc_config("Spooler", "disabled"))),

            # WSearch disabled safely — does NOT break login/Windows Search UI,
            # only background indexing. 
            ("Disable WSearch background indexer",
             lambda: (sc_stop("WSearch"), sc_config("WSearch", "disabled"))),

            ("Disable visual effects (best performance)",
             lambda: reg_add(
                 r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                 "VisualFXSetting", "REG_DWORD", 2
             )),

            ("Menu show delay → 0ms",
             lambda: reg_add(
                 r"HKCU\Control Panel\Desktop", "MenuShowDelay", "REG_SZ", 0
             )),

            ("Disable Windows Tips (toast)",
             lambda: reg_add(
                 r"HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications",
                 "ToastEnabled", "REG_DWORD", 0
             )),

            ("Foreground app priority",
             lambda: reg_add(
                 r"HKCU\Control Panel\Desktop",
                 "ForegroundFlashCount", "REG_DWORD", 2
             )),

            ("Disable Cortana",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                 "AllowCortana", "REG_DWORD", 0
             )),

            ("System responsiveness boost",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
                 "SystemResponsiveness", "REG_DWORD", 1
             )),

            ("Large System Cache",
             lambda: reg_add(
                 r"HKLM\System\CurrentControlSet\Control\Session Manager\Memory Management",
                 "LargeSystemCache", "REG_DWORD", 1
             )),

            ("TCP AutoTuning disabled",
             lambda: run_cmd(
                 ["netsh", "int", "tcp", "set", "global", "autotuninglevel=disabled"]
             )),

            ("TCP RSC disabled",
             lambda: run_cmd(
                 ["netsh", "int", "tcp", "set", "global", "rsc=disabled"]
             )),

            ("Flush DNS",
             lambda: run_cmd(["ipconfig", "/flushdns"])),

            ("Disable automatic Windows Update",
             lambda: reg_add(
                 r"HKLM\Software\Policies\Microsoft\Windows\WindowsUpdate\AU",
                 "NoAutoUpdate", "REG_DWORD", 1
             )),

            ("Pagefile: 8192–16384 MB",
             lambda: (
                 run_cmd(["wmic", "computersystem", "where",
                          f"name=\"{os.environ.get('COMPUTERNAME','localhost')}\"",
                          "set", "AutomaticManagedPagefile=False"]),
                 run_cmd(["wmic", "pagefile", "set",
                          "InitialSize=8192,MaximumSize=16384"])
             )),
        ]
        self._run_tasks(tasks, log, set_prog)

    # Low Latency 2
    def _apply_ll2_tweaks(self, log, set_prog):
        tasks = [
            ("No lock screen",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization",
                 "NoLockScreen", "REG_DWORD", 1
             )),

            ("Disable driver auto-search",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching",
                 "SearchOrderConfig", "REG_DWORD", 0
             )),

            ("Disable consumer features",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent",
                 "DisableWindowsConsumerFeatures", "REG_DWORD", 1
             )),

            ("MMCSS NetworkThrottlingIndex",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
                 "NetworkThrottlingIndex", "REG_DWORD", 4294967295
             )),

            ("MMCSS SystemResponsiveness → 0",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
                 "SystemResponsiveness", "REG_DWORD", 0
             )),

            ("MMCSS Games: GPU Priority 8 / CPU Priority 6",
             lambda: [
                 reg_add(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
                         k, t, v)
                 for k, t, v in [
                     ("GPU Priority",        "REG_DWORD", 8),
                     ("Priority",            "REG_DWORD", 6),
                     ("Scheduling Category", "REG_SZ",    "High"),
                     ("SFIO Priority",       "REG_SZ",    "High"),
                     ("Clock Rate",          "REG_DWORD", 10000),
                     ("Background Only",     "REG_SZ",    "False"),
                     ("Affinity",            "REG_DWORD", 0),
                 ]
             ]),

            ("Disable Power Throttling",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
                 "PowerThrottlingOff", "REG_DWORD", 1
             )),

            ("Disable GameDVR / Xbox DVR",
             lambda: [
                 reg_add(r"HKCU\System\GameConfigStore", k, "REG_DWORD", v)
                 for k, v in [
                     ("GameDVR_Enabled", 0),
                     ("GameDVR_FSEBehaviorMode", 2),
                     ("GameDVR_HonorUserFSEBehaviorMode", 0),
                     ("GameDVR_DXGIHonorFSEWindowsCompatible", 1),
                     ("GameDVR_EFSEFeatureFlags", 0),
                 ]
             ]),

            ("Disable hibernation",
             lambda: (
                 reg_add(r"HKLM\SYSTEM\CurrentControlSet\Control\Power",
                         "HibernateEnabled", "REG_DWORD", 0),
                 run_cmd(["powercfg", "-h", "off"])
             )),

            ("Kill-timeout tweaks (HungApp, WaitToKill)",
             lambda: [
                 reg_add(r"HKCU\Control Panel\Desktop", k, "REG_SZ", v)
                 for k, v in [
                     ("AutoEndTasks",        "1"),
                     ("HungAppTimeout",      "1000"),
                     ("WaitToKillAppTimeout","2000"),
                     ("LowLevelHooksTimeout","1000"),
                     ("MenuShowDelay",       "0"),
                 ]
             ]),

            ("Service kill timeout → 2000ms",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Control",
                 "WaitToKillServiceTimeout", "REG_SZ", "2000"
             )),

            ("Disable auto-maintenance",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance",
                 "MaintenanceDisabled", "REG_DWORD", 1
             )),

            ("Hardware GPU Scheduling (HAGS)",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
                 "HwSchMode", "REG_DWORD", 2
             )),

            ("Disable Variable Refresh Rate",
             lambda: reg_add(
                 r"HKCU\SOFTWARE\Microsoft\DirectX\UserGpuPreferences",
                 "DirectXUserGlobalSettings", "REG_SZ", "VRROptimizeEnable=0;"
             )),

            ("Disable Ease of Access shortcuts",
             lambda: [
                 reg_add(path, "Flags", "REG_SZ", "0")
                 for path in [
                     r"HKCU\Control Panel\Accessibility\MouseKeys",
                     r"HKCU\Control Panel\Accessibility\StickyKeys",
                     r"HKCU\Control Panel\Accessibility\Keyboard Response",
                     r"HKCU\Control Panel\Accessibility\ToggleKeys",
                 ]
             ]),

            ("Privacy: disable advertising ID",
             lambda: reg_add(
                 r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
                 "Enabled", "REG_DWORD", 0
             )),

            ("Privacy: disable location access",
             lambda: reg_add(
                 r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location",
                 "Value", "REG_SZ", "Deny"
             )),

            ("Privacy: disable telemetry",
             lambda: (
                 reg_add(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                         "AllowTelemetry", "REG_DWORD", 0),
                 reg_add(r"HKLM\SYSTEM\CurrentControlSet\Services\DiagTrack",
                         "Start", "REG_DWORD", 4),
             )),

            ("Disable background apps",
             lambda: [
                 reg_add(path, k, "REG_DWORD", 1)
                 for path, k in [
                     (r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
                      "GlobalUserDisabled"),
                 ]
             ]),

            ("Mouse acceleration OFF",
             lambda: [
                 reg_add(r"HKU\.DEFAULT\Control Panel\Mouse", k, "REG_SZ", "0")
                 for k in ["MouseSpeed", "MouseThreshold1", "MouseThreshold2"]
             ]),

            ("Win32PrioritySeparation optimal",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl",
                 "Win32PrioritySeparation", "REG_DWORD", 40
             )),

            ("Disable Xbox Live services",
             lambda: [
                 reg_add(
                     f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\{svc}",
                     "Start", "REG_DWORD", 4
                 )
                 for svc in ["XblGameSave", "XboxNetApiSvc", "XboxGipSvc", "XblAuthManager"]
             ]),

            ("Disable Bluetooth services",
             lambda: [
                 reg_add(
                     f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\{svc}",
                     "Start", "REG_DWORD", 4
                 )
                 for svc in ["BTAGService", "bthserv"]
             ]),

            ("AMD GPU: disable power gating & stutter",
             lambda: [
                 reg_add(
                     r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                     k, "REG_DWORD", v
                 )
                 for k, v in [
                     ("EnableUlps", 0),
                     ("StutterMode", 0),
                     ("PP_SclkDeepSleepDisable", 1),
                     ("PP_ThermalAutoThrottlingEnable", 0),
                     ("DisableDrmdmaPowerGating", 1),
                     ("DisablePowerGating", 1),
                     ("DisableDMACopy", 1),
                     ("DisableAllClockGating", 1),
                 ]
             ]),

            ("Disable GPU preemption",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Scheduler",
                 "EnablePreemption", "REG_DWORD", 0
             )),

            ("DNS resolver priorities",
             lambda: [
                 reg_add(r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider",
                         k, "REG_DWORD", v)
                 for k, v in [
                     ("DnsPriority", 6), ("HostsPriority", 5),
                     ("LocalPriority", 4), ("NetbtPriority", 7),
                 ]
             ]),

            ("BCDEdit: timer resolution tweaks",
             lambda: [
                 run_cmd(["bcdedit", "/set", k, v])
                 for k, v in [
                     ("disabledynamictick", "yes"),
                     ("useplatformtick", "yes"),
                 ]
             ]),
        ]
        self._run_tasks(tasks, log, set_prog)

    # Tweaks Pack 3
    def _apply_tweaks3(self, log, set_prog):
        tasks = [
            ("Disable window animations",
             lambda: [
                 reg_add(
                     r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                     "VisualFXSetting", "REG_DWORD", 2
                 ),
                 reg_add(
                     r"HKCU\Control Panel\Desktop\WindowMetrics",
                     "MinAnimate", "REG_SZ", "0"
                 ),
             ]),

            ("Remove lock screen",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization",
                 "NoLockScreen", "REG_DWORD", 1
             )),

            ("Startup delay → 0ms",
             lambda: reg_add(
                 r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize",
                 "StartupDelayInMSec", "REG_DWORD", 0
             )),

            ("Enable fast startup / hibernate on",
             lambda: run_cmd(["powercfg", "/hibernate", "on"])),

            ("Standby & display timeout → 0 (AC)",
             lambda: [
                 run_cmd(["powercfg", "/change", f"/standby-timeout-ac", "0"]),
                 run_cmd(["powercfg", "/change", f"/disp-timeout-ac", "0"]),
             ]),

            ("Standby & display timeout → 0 (DC)",
             lambda: [
                 run_cmd(["powercfg", "/change", "/standby-timeout-dc", "0"]),
                 run_cmd(["powercfg", "/change", "/disp-timeout-dc", "0"]),
             ]),
        ]
        self._run_tasks(tasks, log, set_prog)

    # Tweaks Pack 4
    def _apply_tweaks4(self, log, set_prog):
        tasks = [
            ("Clean temp files",
             lambda: run_cmd(["cmd", "/c", "del /s /q %temp%\\*"], shell=False)),

            ("Disable OneDrive from startup",
             lambda: reg_add(
                 r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
                 "OneDrive", "REG_SZ", " "
             )),

            ("Disable Skype from startup",
             lambda: reg_add(
                 r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
                 "Skype", "REG_SZ", " "
             )),

            ("Visual effects → best performance",
             lambda: reg_add(
                 r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                 "VisualFXSetting", "REG_DWORD", 3
             )),

            ("High Performance power plan",
             lambda: run_cmd(["powercfg", "-setactive", "SCHEME_MIN"])),

            ("Disable SysMain",
             lambda: (sc_config("SysMain", "disabled"), sc_stop("SysMain"))),

            ("Disable DiagTrack (telemetry)",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Services\DiagTrack",
                 "Start", "REG_DWORD", 4
             )),

            ("Disable dmwappushservice",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Services\dmwappushservice",
                 "Start", "REG_DWORD", 4
             )),

            ("Disable hibernation",
             lambda: run_cmd(["powercfg", "-h", "off"])),

            ("Flush DNS cache",
             lambda: run_cmd(["ipconfig", "/flushdns"])),

            ("Disable Windows Tips (content delivery)",
             lambda: [
                 reg_add(
                     r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                     k, "REG_DWORD", 0
                 )
                 for k in [
                     "SubscribedContent-338389Enabled",
                     "SubscribedContent-353694Enabled",
                 ]
             ]),

            ("Disable remote assistance",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Control\Remote Assistance",
                 "fAllowToGetHelp", "REG_DWORD", 0
             )),

            ("Menu show delay → 20ms",
             lambda: reg_add(
                 r"HKCU\Control Panel\Desktop",
                 "MenuShowDelay", "REG_SZ", "20"
             )),

            ("Disable background apps globally",
             lambda: reg_add(
                 r"HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
                 "GlobalUserDisabled", "REG_DWORD", 1
             )),

            ("Disable Cortana",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                 "AllowCortana", "REG_DWORD", 0
             )),

            ("Disable telemetry",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                 "AllowTelemetry", "REG_DWORD", 0
             )),

            ("Disable Windows Error Reporting",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting",
                 "Disabled", "REG_DWORD", 1
             )),

            ("Shutdown time → 5000ms",
             lambda: reg_add(
                 r"HKLM\SYSTEM\CurrentControlSet\Control",
                 "WaitToKillServiceTimeout", "REG_SZ", "5000"
             )),

            ("Disable indexer backoff",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows Search",
                 "DisableBackoff", "REG_DWORD", 1
             )),

            ("Disable automatic driver updates",
             lambda: reg_add(
                 r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching",
                 "SearchOrderConfig", "REG_DWORD", 0
             )),
        ]
        self._run_tasks(tasks, log, set_prog)

    # Task Runner
    def _run_tasks(self, tasks, log, set_prog):
        total = len(tasks)
        for i, (name, fn) in enumerate(tasks):
            self.after(0, lambda v=(i + 1) / total: set_prog(v))
            try:
                fn()
                self._log(log, f"✔  {name}")
            except Exception as e:
                self._log(log, f"✘  {name} — {e}")
        self._log(log, "=== COMPLETE — RESTART FOR FULL EFFECT ===")


# Entry
if __name__ == "__main__":
    app = NZSVOptimizer()
    app.mainloop()