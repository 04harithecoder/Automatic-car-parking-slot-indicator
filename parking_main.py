"""
╔══════════════════════════════════════════════════════════╗
║   AUTOMATIC CAR PARKING SLOT INDICATOR           ║
║   Frontend : Python Tkinter                              ║
║   Database : MySQL (parking_db)                          ║
║   Backend  : Emu8086 / DOSBox (runs independently)       ║
╚══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import font as tkfont, messagebox
import math, time, threading, subprocess
import db_manager as db

try:
    import win32gui, win32con
    PYWIN32_OK = True
except ImportError:
    PYWIN32_OK = False
    print("[pywin32] Not installed — install with: pip install pywin32")

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False
    print("[pyautogui] Not installed — install with: pip install pyautogui")

# ─────────────────────────────────────────────────────────────
#   DOSBOX CONFIG — change paths if needed
# ─────────────────────────────────────────────────────────────
DOSBOX_PATH     = r"C:\Program Files (x86)\DOSBox-0.74-3\DOSBox.exe"
ASSEMBLY_FOLDER = r"C:\Users\HP\Music\MCMP PROJECT"

def launch_dosbox():
    """Auto-launch DOSBox and run parking.com on startup."""
    try:
        subprocess.Popen([
            DOSBOX_PATH,
            "-c", f"mount c \"{ASSEMBLY_FOLDER}\"",
            "-c", "c:",
            "-c", "parking.com",
        ])
        print("[DOSBox] Launched successfully!")
    except FileNotFoundError:
        print(f"[DOSBox] Not found at {DOSBOX_PATH} — open manually!")


def _find_dosbox_hwnd():
    """Find DOSBox window handle by title."""
    result = []
    def _enum(hwnd, _):
        title = win32gui.GetWindowText(hwnd).lower()
        if "dosbox" in title and win32gui.IsWindowVisible(hwnd):
            result.append(hwnd)
    win32gui.EnumWindows(_enum, None)
    return result[0] if result else None


def send_keys_to_dosbox(keys: str, delay_ms: int = 120):
    """
    Focus the DOSBox window using pywin32, then use pyautogui
    to send real OS-level keystrokes that SDL/DOSBox can receive.
    keys format: plain chars + '<ENTER>' token.
    Runs in a background thread.
    """
    if not PYWIN32_OK or not PYAUTOGUI_OK:
        print("[DOSBox Sync] pywin32 or pyautogui missing — skipping.")
        return

    def _send():
        time.sleep(0.5)   # brief pause so DB write finishes first

        hwnd = _find_dosbox_hwnd()
        if not hwnd:
            print("[DOSBox Sync] DOSBox window not found!")
            return

        # ── Bring DOSBox to foreground ──────────────────────
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.4)   # wait for focus to settle

        # ── Send keystrokes via pyautogui ───────────────────
        # Split on <ENTER> and send each part with a generous
        # pause AFTER each Enter — DOS buffered input (INT 21h/0Ah)
        # needs time to re-arm before it can accept the next input!
        parts = keys.split("<ENTER>")
        for i, part in enumerate(parts):
            if part:
                pyautogui.typewrite(part, interval=delay_ms / 1000.0)
            if i < len(parts) - 1:
                pyautogui.press("enter")
                time.sleep(1.2)   
        print(f"[DOSBox Sync] Sent: {repr(keys)}")

    threading.Thread(target=_send, daemon=True).start()

MAX_SLOTS   = 10
BG          = "#0D0F14"
PANEL       = "#141720"
CARD        = "#1C2030"
BORDER      = "#2A3050"
ACCENT_BLUE = "#4F8EF7"
ACCENT_GRN  = "#2ECC8A"
ACCENT_RED  = "#E84545"
ACCENT_YLW  = "#F5A623"
ACCENT_PRP  = "#A855F7"
TEXT_PRI    = "#E8EAF0"
TEXT_SEC    = "#7A8299"
TEXT_DIM    = "#3D4460"


class EntryPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Vehicle Entry — Details")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(bg=CARD)
        self.grab_set()
        self.result = None
        f_lbl = tkfont.Font(family="Courier New", size=10)
        f_hd  = tkfont.Font(family="Courier New", size=12, weight="bold")
        f_btn = tkfont.Font(family="Courier New", size=11, weight="bold")
        tk.Frame(self, bg=ACCENT_BLUE, height=4).pack(fill="x")
        tk.Label(self, text="  ▲  VEHICLE ENTRY DETAILS",
                 font=f_hd, bg=CARD, fg=TEXT_PRI, anchor="w").pack(fill="x", padx=20, pady=(16,12))
        fields = [("Owner Name",20,"name"),("Phone Number",13,"phone"),("Vehicle No",15,"vehno")]
        self.vars = {}
        for label, maxlen, key in fields:
            row = tk.Frame(self, bg=CARD)
            row.pack(fill="x", padx=20, pady=6)
            tk.Label(row, text=f"{label:<14}:", font=f_lbl, bg=CARD, fg=TEXT_SEC,
                     width=16, anchor="w").pack(side="left")
            var = tk.StringVar()
            ent = tk.Entry(row, textvariable=var, font=f_lbl, bg=BG, fg=TEXT_PRI,
                           insertbackground=TEXT_PRI, relief="flat", width=22)
            ent.pack(side="left", ipady=4, padx=(4,0))
            ent.config(validate="key",
                       validatecommand=(self.register(lambda s,m=maxlen: len(s)<=m),"%P"))
            self.vars[key] = var
        btns = tk.Frame(self, bg=CARD)
        btns.pack(fill="x", padx=20, pady=(16,0))
        tk.Button(btns, text="✔  CONFIRM", font=f_btn, bg=ACCENT_BLUE, fg="white",
                  relief="flat", cursor="hand2", pady=8,
                  command=self._confirm).pack(side="left", expand=True, fill="x", padx=(0,6))
        tk.Button(btns, text="✘  CANCEL", font=f_btn, bg="#2A2A3A", fg=TEXT_SEC,
                  relief="flat", cursor="hand2", pady=8,
                  command=self.destroy).pack(side="left", expand=True, fill="x", padx=(6,0))

    def _confirm(self):
        name=self.vars["name"].get().strip()
        phone=self.vars["phone"].get().strip()
        vehno=self.vars["vehno"].get().strip()
        if not name and not phone and not vehno:
            messagebox.showwarning("Missing Info","Please fill all fields!",parent=self)
            return
        self.result={"name":name,"phone":phone,"vehno":vehno}
        self.destroy()


class ExitPopup(tk.Toplevel):
    def __init__(self, parent, slots):
        super().__init__(parent)
        self.title("Vehicle Exit — Select Slot")
        self.geometry("460x320")
        self.resizable(False, False)
        self.configure(bg=CARD)
        self.grab_set()
        self.result = None
        f_hd  = tkfont.Font(family="Courier New", size=12, weight="bold")
        f_lbl = tkfont.Font(family="Courier New", size=9)
        f_sm  = tkfont.Font(family="Courier New", size=8)
        tk.Frame(self, bg=ACCENT_YLW, height=4).pack(fill="x")
        tk.Label(self, text="  ▼  SELECT SLOT TO FREE", font=f_hd, bg=CARD,
                 fg=TEXT_PRI, anchor="w").pack(fill="x", padx=20, pady=(16,4))
        tk.Label(self, text="  Click an occupied slot (red) to release:",
                 font=f_lbl, bg=CARD, fg=TEXT_SEC, anchor="w").pack(fill="x", padx=20, pady=(0,12))
        grid = tk.Frame(self, bg=CARD)
        grid.pack(padx=20, fill="x")
        for i, slot in enumerate(slots):
            col=i%5; row=i//5
            if slot["is_occupied"]:
                short=slot["vehicle_no"][:6] if slot["vehicle_no"] else "OCC"
                btn=tk.Button(grid, text=f"P{slot['slot_id']}\n{short}", font=f_sm,
                    bg=ACCENT_RED, fg="white", relief="flat", cursor="hand2",
                    width=7, height=3, command=lambda s=slot["slot_id"]: self._pick(s))
            else:
                btn=tk.Button(grid, text=f"P{slot['slot_id']}\nFREE", font=f_sm,
                    bg="#1C2030", fg=TEXT_DIM, relief="flat", state="disabled", width=7, height=3)
            btn.grid(row=row, column=col, padx=5, pady=5)
        tk.Button(self, text="CANCEL", font=f_lbl, bg="#2A2A3A", fg=TEXT_SEC,
                  relief="flat", cursor="hand2", pady=6,
                  command=self.destroy).pack(pady=(10,0))

    def _pick(self, slot_id):
        self.result=slot_id
        self.destroy()


class SlotDetailPopup(tk.Toplevel):
    def __init__(self, parent, slot):
        super().__init__(parent)
        self.title(f"Slot P{slot['slot_id']} Details")
        self.geometry("340x240")
        self.resizable(False, False)
        self.configure(bg=CARD)
        self.grab_set()
        f_hd=tkfont.Font(family="Courier New", size=11, weight="bold")
        f_lbl=tkfont.Font(family="Courier New", size=10)
        tk.Frame(self, bg=ACCENT_BLUE, height=4).pack(fill="x")
        tk.Label(self, text=f"  SLOT P{slot['slot_id']} — VEHICLE RECORD",
                 font=f_hd, bg=CARD, fg=TEXT_PRI, anchor="w").pack(fill="x", padx=16, pady=(14,10))
        entry_str=str(slot["entry_time"]) if slot["entry_time"] else "—"
        for label, val in [("Owner Name",slot.get("owner_name","—")),
                           ("Phone No",slot.get("phone","—")),
                           ("Vehicle No",slot.get("vehicle_no","—")),
                           ("Entry Time",entry_str)]:
            row=tk.Frame(self, bg=CARD)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=f"{label}:", font=f_lbl, bg=CARD, fg=TEXT_SEC,
                     width=14, anchor="w").pack(side="left")
            tk.Label(row, text=val or "—", font=f_lbl, bg=CARD, fg=TEXT_PRI,
                     anchor="w").pack(side="left")
        tk.Button(self, text="CLOSE", font=f_lbl, bg="#2A2A3A", fg=TEXT_SEC,
                  relief="flat", cursor="hand2", pady=6,
                  command=self.destroy).pack(pady=(12,0))


class ParkingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Car Parking Slot Indicator v3.0")
        self.geometry("720x740")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._load_fonts()
        self._build_header()
        self._build_db_status_bar()
        self._build_slot_display()
        self._build_slot_grid()
        self._build_controls()
        self._build_log()
        self._build_footer()
        self._animate_pulse()
        self._refresh_from_db()
        self._poll_emu_file()
        # Auto-launch DOSBox with parking.com!
        threading.Thread(target=launch_dosbox, daemon=True).start()

    def _load_fonts(self):
        self.f_title  = tkfont.Font(family="Courier New", size=13, weight="bold")
        self.f_big    = tkfont.Font(family="Courier New", size=54, weight="bold")
        self.f_label  = tkfont.Font(family="Courier New", size=9)
        self.f_btn    = tkfont.Font(family="Courier New", size=12, weight="bold")
        self.f_status = tkfont.Font(family="Courier New", size=11, weight="bold")

    def _build_header(self):
        hdr=tk.Frame(self, bg=PANEL, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ACCENT_BLUE, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text="AUTOMATIC CAR PARKING SLOT INDICATOR",
                 font=self.f_title, bg=PANEL, fg=TEXT_PRI, padx=18).pack(side="left")
        self.clock_var=tk.StringVar()
        tk.Label(hdr, textvariable=self.clock_var, font=self.f_label,
                 bg=PANEL, fg=TEXT_SEC, padx=18).pack(side="right")
        self._tick_clock()

    def _build_db_status_bar(self):
        bar=tk.Frame(self, bg="#0A0C10", height=30)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        self.db_dot_c=tk.Canvas(bar, width=14, height=14, bg="#0A0C10", highlightthickness=0)
        self.db_dot_c.pack(side="left", padx=(12,4), pady=8)
        self.db_dot=self.db_dot_c.create_oval(2,2,12,12, fill=ACCENT_YLW, outline="")
        self.db_var=tk.StringVar(value="Connecting to MySQL...")
        tk.Label(bar, textvariable=self.db_var,
                 font=tkfont.Font(family="Courier New", size=9, weight="bold"),
                 bg="#0A0C10", fg=TEXT_SEC).pack(side="left")

    def _build_slot_display(self):
        outer=tk.Frame(self, bg=BG)
        outer.pack(fill="x", padx=24, pady=(16,0))
        left=tk.Frame(outer, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", expand=True, fill="both", padx=(0,8))
        tk.Label(left, text="AVAILABLE SLOTS", font=self.f_label, bg=CARD, fg=TEXT_SEC).pack(pady=(14,0))
        self.count_label=tk.Label(left, text="--", font=self.f_big, bg=CARD, fg=ACCENT_GRN)
        self.count_label.pack()
        tk.Label(left, text=f"of {MAX_SLOTS} total", font=self.f_label, bg=CARD, fg=TEXT_DIM).pack(pady=(0,14))
        right=tk.Frame(outer, bg=CARD, width=200, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="both", padx=(8,0))
        right.pack_propagate(False)
        tk.Label(right, text="STATUS", font=self.f_label, bg=CARD, fg=TEXT_SEC).pack(pady=(14,8))
        self.status_canvas=tk.Canvas(right, width=50, height=50, bg=CARD, highlightthickness=0)
        self.status_canvas.pack()
        self.pulse_oval=self.status_canvas.create_oval(8,8,42,42, fill=ACCENT_GRN, outline="")
        self.status_label=tk.Label(right, text="OPEN", font=self.f_status, bg=CARD, fg=ACCENT_GRN)
        self.status_label.pack(pady=(6,0))
        self.occupied_label=tk.Label(right, text="0 occupied", font=self.f_label, bg=CARD, fg=TEXT_SEC)
        self.occupied_label.pack(pady=(4,14))

    def _build_slot_grid(self):
        wrapper=tk.Frame(self, bg=BG)
        wrapper.pack(fill="x", padx=24, pady=(14,0))
        tk.Label(wrapper, text="SLOT MAP  (click occupied slot for details)",
                 font=self.f_label, bg=BG, fg=TEXT_SEC, anchor="w").pack(fill="x", pady=(0,6))
        grid_frame=tk.Frame(wrapper, bg=BG)
        grid_frame.pack(fill="x")
        self.slot_boxes=[]
        for i in range(MAX_SLOTS):
            box=tk.Canvas(grid_frame, width=57, height=50, bg=CARD,
                          highlightthickness=1, highlightbackground=ACCENT_GRN, cursor="hand2")
            box.grid(row=0, column=i, padx=3)
            box.create_rectangle(4,4,53,46, fill="#1A2E20", outline="", tags="fill")
            lbl=box.create_text(29,22, text=f"P{i+1}", font=self.f_label, fill=ACCENT_GRN, tags="lbl")
            sub=box.create_text(29,38, text="FREE",
                                font=tkfont.Font(family="Courier New", size=7),
                                fill=TEXT_DIM, tags="sub")
            box.bind("<Button-1>", lambda e, idx=i: self._slot_clicked(idx))
            self.slot_boxes.append((box,lbl,sub))

    def _build_controls(self):
        ctrl=tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", padx=24, pady=16)
        self.btn_entry=tk.Button(ctrl, text="▲  VEHICLE ENTRY",
            font=self.f_btn, bg=ACCENT_BLUE, fg="white",
            activebackground="#3A6FD8", relief="flat", cursor="hand2",
            pady=14, command=self.vehicle_entry)
        self.btn_entry.pack(side="left", expand=True, fill="x", padx=(0,8))
        self.btn_exit=tk.Button(ctrl, text="▼  VEHICLE EXIT",
            font=self.f_btn, bg=ACCENT_YLW, fg="#0D0F14",
            activebackground="#D4901F", relief="flat", cursor="hand2",
            pady=14, command=self.vehicle_exit)
        self.btn_exit.pack(side="left", expand=True, fill="x", padx=(8,0))

    def _build_log(self):
        wrapper=tk.Frame(self, bg=BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=(0,8))
        tk.Label(wrapper, text="ACTIVITY LOG", font=self.f_label, bg=BG,
                 fg=TEXT_SEC, anchor="w").pack(fill="x", pady=(0,4))
        log_frame=tk.Frame(wrapper, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        log_frame.pack(fill="both", expand=True)
        self.log_text=tk.Text(log_frame, bg=CARD, fg=TEXT_SEC, font=self.f_label,
                              relief="flat", state="disabled", padx=10, pady=8, wrap="word", height=7)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("entry", foreground=ACCENT_BLUE)
        self.log_text.tag_config("exit",  foreground=ACCENT_YLW)
        self.log_text.tag_config("full",  foreground=ACCENT_RED)
        self.log_text.tag_config("info",  foreground=TEXT_SEC)
        self.log_text.tag_config("ok",    foreground=ACCENT_GRN)
        self.log_text.tag_config("db",    foreground=ACCENT_PRP)

    def _build_footer(self):
        foot=tk.Frame(self, bg=PANEL, height=28)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)
        tk.Label(foot,
                 text="  Backend: Emu8086 Assembly  |  DB: MySQL parking_db  |  Frontend: Tkinter  v3.0",
                 font=self.f_label, bg=PANEL, fg=TEXT_DIM).pack(side="left")

    def vehicle_entry(self):
        slots=db.get_all_slots()
        avail=sum(1 for s in slots if not s["is_occupied"])
        if avail<=0:
            self._log(f"[{self._ts()}]  ENTRY DENIED — Parking FULL!","full")
            self._flash_full()
            return
        popup=EntryPopup(self)
        self.wait_window(popup)
        if popup.result is None:
            return
        data=popup.result
        def _do():
            slot_id=db.enter_vehicle(data["name"],data["phone"],data["vehno"])
            self.after(0, lambda: self._on_entry_done(slot_id,data))
        threading.Thread(target=_do, daemon=True).start()

    def _on_entry_done(self, slot_id, data):
        if slot_id is None:
            self._log(f"[{self._ts()}]  DB Error on entry!","full")
            return
        self._log(f"[{self._ts()}]  ▲ ENTRY — Slot P{slot_id} | {data['name']} | {data['phone']} | {data['vehno']}","entry")
        self._log(f"[{self._ts()}]  ◆ Saved to MySQL parking_db ✔","db")
        self._flash_button(self.btn_entry, ACCENT_BLUE)
        avail = db.get_available_count()
        self._write_park_txt(avail, cmd="ENTRY")
        self._log(f"[{self._ts()}]  ⇒ park.txt updated → CMD=ENTRY","info")
        self._refresh_from_db()

    def vehicle_exit(self):
        slots=db.get_all_slots()
        if not any(s["is_occupied"] for s in slots):
            self._log(f"[{self._ts()}]  EXIT IGNORED — No vehicles present.","info")
            return
        popup=ExitPopup(self, slots)
        self.wait_window(popup)
        if popup.result is None:
            return
        slot_id=popup.result
        def _do():
            success=db.exit_vehicle(slot_id)
            self.after(0, lambda: self._on_exit_done(slot_id,success))
        threading.Thread(target=_do, daemon=True).start()

    def _on_exit_done(self, slot_id, success):
        if not success:
            self._log(f"[{self._ts()}]  DB Error on exit!","full")
            return
        self._log(f"[{self._ts()}]  ▼ EXIT  — Slot P{slot_id} freed","exit")
        self._log(f"[{self._ts()}]  ◆ Updated in MySQL parking_db ✔","db")
        self._flash_button(self.btn_exit, ACCENT_YLW)
        avail = db.get_available_count()
        self._write_park_txt(avail, cmd="EXIT")
        self._log(f"[{self._ts()}]  ⇒ park.txt updated → CMD=EXIT","info")
        self._refresh_from_db()

    def _slot_clicked(self, idx):
        slots=db.get_all_slots()
        slot=slots[idx]
        if not slot["is_occupied"]:
            return
        SlotDetailPopup(self, slot)

    def _refresh_from_db(self):
        def _fetch():
            try:
                slots=db.get_all_slots()
                self.after(0, lambda: self._apply_slots(slots))
                self.after(0, lambda: self._set_db_status(True))
            except Exception as e:
                self.after(0, lambda: self._set_db_status(False,str(e)))
        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_slots(self, slots):
        # Slot grid colours + vehicle details from MySQL
        # Big counter is handled by _poll_emu_file from park.txt
        self._apply_slot_grid(slots)

    def _write_park_txt(self, avail, cmd="NONE"):
        """
        Python writes park.txt after every Entry/Exit/Quit.
        ASM polls this file and reacts to the CMD field.
        cmd values: ENTRY | EXIT | QUIT | NONE
        """
        STATUS_FILE = r"C:\Users\HP\Music\MCMP PROJECT\park.txt"
        status = "FULL" if avail == 0 else "OPEN"
        try:
            with open(STATUS_FILE, "w") as f:
                f.write(f"AVAILABLE={avail:2d}\n")
                f.write(f"STATUS={status}\n")
                f.write(f"CMD={cmd}\n")
            print(f"[park.txt] Written → AVAILABLE={avail} STATUS={status} CMD={cmd}")
        except Exception as e:
            print(f"[park.txt] Write error: {e}")

    def _set_db_status(self, ok, err=""):
        if ok:
            self.db_dot_c.itemconfig(self.db_dot, fill=ACCENT_GRN)
            self.db_var.set("✔  MySQL parking_db connected")
        else:
            self.db_dot_c.itemconfig(self.db_dot, fill=ACCENT_RED)
            self.db_var.set(f"✘  DB Error: {err[:60]}")

    def _animate_pulse(self):
        t=time.time()
        alpha=0.55+0.45*math.sin(t*3)
        base=(46,204,138)
        col="#{:02X}{:02X}{:02X}".format(
            int(base[0]*alpha+13*(1-alpha)),
            int(base[1]*alpha+15*(1-alpha)),
            int(base[2]*alpha+20*(1-alpha)))
        self.status_canvas.itemconfig(self.pulse_oval, fill=col)
        self.after(50, self._animate_pulse)

    def _flash_button(self, btn, col):
        btn.config(bg="white")
        self.after(120, lambda: btn.config(bg=col))

    def _flash_full(self):
        self.count_label.config(fg="white")
        self.after(150, lambda: self.count_label.config(fg=ACCENT_RED))

    def _log(self, msg, tag="info"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg+"\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _tick_clock(self):
        self.clock_var.set(time.strftime("  %d %b %Y   %H:%M:%S  "))
        self.after(1000, self._tick_clock)

    def _ts(self):
        return time.strftime("%H:%M:%S")

    # ═════════════════════════════════════════════════════════
    #   EMU FILE POLL — park.txt is master for slot count
    #   Runs every 500ms — updates big counter + status
    #   MySQL gives vehicle details for slot grid
    # ═════════════════════════════════════════════════════════
    def _poll_emu_file(self):
        STATUS_FILE = r"C:\Users\HP\Music\MCMP PROJECT\park.txt"
        try:
            with open(STATUS_FILE, "r") as f:
                lines = f.readlines()

            data = {}
            for line in lines:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip()

            avail  = int(data.get("AVAILABLE", -1))
            status = data.get("STATUS", "OPEN").strip()

            if avail >= 0:
                occupied = MAX_SLOTS - avail
                ratio    = avail / MAX_SLOTS

                # ── Big counter (from park.txt) ───────────
                col = ACCENT_GRN if ratio > 0.5 else \
                      (ACCENT_YLW if ratio > 0.2 else ACCENT_RED)
                self.count_label.config(text=str(avail), fg=col)
                self.occupied_label.config(text=f"{occupied} occupied")

                # ── Status dot + label (from park.txt) ───
                if status == "FULL" or avail == 0:
                    self.status_label.config(text="FULL", fg=ACCENT_RED)
                    self.status_canvas.itemconfig(self.pulse_oval, fill=ACCENT_RED)
                    self.btn_entry.config(state="disabled", bg="#2A2A3A", fg=TEXT_DIM)
                else:
                    self.status_label.config(text="OPEN", fg=ACCENT_GRN)
                    self.status_canvas.itemconfig(self.pulse_oval, fill=ACCENT_GRN)
                    self.btn_entry.config(state="normal", bg=ACCENT_BLUE, fg="white")

                # ── Status bar ────────────────────────────
                self.db_var.set(
                    f"✔  MySQL: vehicle details  |  ◆ DOSBox: {avail} slots — {status}")
                self.db_dot_c.itemconfig(self.db_dot, fill=ACCENT_PRP)

                # ── Slot grid — vehicle details from MySQL
                #    but count from park.txt ────────────────
                self._refresh_slot_grid_from_db()

        except FileNotFoundError:
            # park.txt not created yet — DOSBox not run
            self.db_var.set("⚠  park.txt not found — Run parking.com in DOSBox!")
        except ValueError:
            pass   # file mid-write, skip this poll
        except Exception as e:
            print(f"[Poll] {e}")

        self.after(500, self._poll_emu_file)

    def _refresh_slot_grid_from_db(self):
        def _fetch():
            try:
                slots = db.get_all_slots()
                self.after(0, lambda: self._apply_slot_grid(slots))
            except Exception as e:
                print(f"[DB Grid] {e}")
        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_slot_grid(self, slots):
        """Update slot grid boxes from MySQL vehicle data."""
        for i, (box, lbl, sub) in enumerate(self.slot_boxes):
            slot = slots[i]
            if slot["is_occupied"]:
                box.configure(highlightbackground=ACCENT_RED)
                box.itemconfig("fill", fill="#2E1A1A")
                box.itemconfig(lbl, fill=ACCENT_RED)
                short = slot["vehicle_no"][:6] if slot["vehicle_no"] else "OCC"
                box.itemconfig(sub, text=short, fill=ACCENT_RED)
            else:
                box.configure(highlightbackground=ACCENT_GRN)
                box.itemconfig("fill", fill="#1A2E20")
                box.itemconfig(lbl, fill=ACCENT_GRN)
                box.itemconfig(sub, text="FREE", fill=TEXT_DIM)


if __name__ == "__main__":
    app = ParkingApp()
    app.mainloop()
