"""The three-month calendar popup."""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from datetime import date
from pathlib import Path

from .icon import apps_are_light
from .weeks import WEEKDAY_ABBR, month_grid, month_offset, month_title

LIGHT_PALETTE = {
    "bg": "#ffffff",
    "border": "#c8c8c8",
    "fg": "#202020",
    "muted": "#a0a0a0",
    "header_fg": "#505050",
    "weekno_fg": "#0067c0",
    "weekno_bg": "#f2f6fb",
    "today_bg": "#0067c0",
    "today_fg": "#ffffff",
}

DARK_PALETTE = {
    "bg": "#2b2b2b",
    "border": "#454545",
    "fg": "#f0f0f0",
    "muted": "#6d6d6d",
    "header_fg": "#b0b0b0",
    "weekno_fg": "#4cc2ff",
    "weekno_bg": "#353535",
    "today_bg": "#4cc2ff",
    "today_fg": "#000000",
}

CELL_FONT = ("Segoe UI", 9)
HEADER_FONT = ("Segoe UI", 9, "bold")
TITLE_FONT = ("Segoe UI", 10, "bold")
TOOLBAR_BUTTON_FONT = ("Segoe UI Symbol", 12, "bold")

CELL_W = 3
PANEL_PAD = 8
# A month spans 4-6 calendar rows; fixing this keeps every panel (and the
# popup's overall height) constant so the sidebar buttons never shift.
MAX_WEEK_ROWS = 6


class _Rect(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def _work_area(fallback_w: int, fallback_h: int):
    """Screen area excluding the taskbar."""
    try:
        rect = _Rect()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    except (AttributeError, OSError):
        pass
    return 0, 0, fallback_w, fallback_h


def _set_caption_buttons(hwnd: int, enable_minmax: bool) -> None:
    """Enable/disable minimize and maximize buttons on a Win32 window."""
    user32 = ctypes.windll.user32
    top = user32.GetParent(hwnd)
    if top:
        hwnd = top
    g = user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE
    if enable_minmax:
        g |= 0x00020000  # WS_MINIMIZEBOX
        g |= 0x00010000  # WS_MAXIMIZEBOX
    else:
        g &= ~0x00020000
        g &= ~0x00010000
    user32.SetWindowLongW(hwnd, -16, g)
    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)  # FRAMECHANGED|NOMOVE|NOSIZE|NOZORDER


def _window_icon_path() -> Path:
    # PyInstaller onefile extracts bundled data under _MEIPASS.
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / "assets" / "septimana.ico"
    return Path(__file__).resolve().parents[1] / "assets" / "septimana.ico"


class CalendarPopup(tk.Toplevel):
    """Calendar window supporting popup mode and normal window mode."""

    def __init__(self, master: tk.Misc, anchor: date | None = None, on_close=None):
        super().__init__(master)
        self.withdraw()
        today = date.today()
        anchor = anchor or today
        self._today = today
        self._year = anchor.year
        self._month = anchor.month
        self._on_close = on_close
        self._c = LIGHT_PALETTE if apps_are_light() else DARK_PALETTE
        self._window_mode = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.configure(bg=self._c["border"])

        self._body = tk.Frame(self, bg=self._c["bg"])
        self._body.pack(padx=1, pady=1)
        self._body.grid_rowconfigure(0, weight=0)
        self._body.grid_columnconfigure(0, weight=0)
        self._body.grid_columnconfigure(1, weight=0)

        self._set_window_icon()

        self._render()
        self._place_near_tray()

        self.bind("<Escape>", lambda _e: self.close())
        self.bind("<FocusOut>", self._on_focus_out)
        # Child widgets carry the toplevel in their bindtags, so this covers the whole popup.
        self.bind("<Double-Button-1>", self._on_double_click)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(10, self._take_focus)

    # -- lifecycle ---------------------------------------------------------

    def _take_focus(self) -> None:
        self.focus_force()

    def _on_focus_out(self, _event) -> None:
        if self._window_mode:
            return
        # Focus may bounce between child widgets; only close if it left the app.
        self.after(1, self._close_if_unfocused)

    def _close_if_unfocused(self) -> None:
        if not self.winfo_exists():
            return
        try:
            focused = self.focus_displayof()
        except KeyError:
            focused = None
        if focused is None and not self._window_mode:
            self.close()

    def present(self) -> None:
        """Show and focus this window; popup mode is repositioned near the tray."""
        if not self.winfo_exists():
            return
        if self._window_mode:
            self.deiconify()
            self.lift()
            self.focus_force()
            return
        self._place_near_tray()
        self.deiconify()
        self.lift()
        self.focus_force()

    def _set_window_mode(self, enabled: bool) -> None:
        if self._window_mode == enabled:
            return
        self._window_mode = enabled

        # Toggling overrideredirect at runtime is more reliable with a withdraw/deiconify cycle.
        geometry = self.geometry()
        self.withdraw()
        self.overrideredirect(not enabled)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.title("Septimana" if enabled else "")
        self.deiconify()
        self.update_idletasks()

        if enabled:
            _set_caption_buttons(self.winfo_id(), False)
            # Tk can still tweak non-client styles on the next idle cycle.
            self.after_idle(lambda: _set_caption_buttons(self.winfo_id(), False))

        if enabled:
            self.geometry(geometry)
        else:
            self._place_near_tray()

        self.lift()
        self.focus_force()

    def _set_window_icon(self) -> None:
        icon = _window_icon_path()
        if not icon.exists():
            return
        try:
            self.iconbitmap(str(icon))
        except tk.TclError:
            pass

    def close(self) -> None:
        if not self.winfo_exists():
            return
        callback, self._on_close = self._on_close, None
        self.destroy()
        if callback:
            callback()

    # -- layout ------------------------------------------------------------

    def _render(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()

        months = tk.Frame(self._body, bg=self._c["bg"])
        months.grid(row=0, column=0, padx=(PANEL_PAD, 0), pady=(PANEL_PAD, 0), sticky="n")

        for offset in (-1, 0, 1):
            year, month = month_offset(self._year, self._month, offset)
            panel = self._build_panel(months, year, month)
            panel.grid(row=0, column=offset + 1, padx=PANEL_PAD, pady=(0, 0), sticky="n")

        toolbar = tk.Frame(self._body, bg=self._c["bg"])
        toolbar.grid(row=0, column=1, padx=0, pady=0, sticky="ns")

        self._sidebar_button(toolbar, self._mode_icon(), self._toggle_mode).grid(
            row=0, column=0, padx=0, pady=0, sticky="ew"
        )
        self._sidebar_button(toolbar, "\u25b6", lambda: self._shift(1)).grid(
            row=1, column=0, padx=0, pady=0, sticky="ew"
        )
        self._sidebar_button(toolbar, "\u25c0", lambda: self._shift(-1)).grid(
            row=2, column=0, padx=0, pady=0, sticky="ew"
        )

    def _build_panel(self, parent: tk.Misc, year: int, month: int) -> tk.Frame:
        panel = tk.Frame(parent, bg=self._c["bg"])

        header = tk.Frame(panel, bg=self._c["bg"])
        header.grid(row=0, column=0, columnspan=8, sticky="ew", pady=(0, 4))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text=month_title(year, month), font=TITLE_FONT,
                 bg=self._c["bg"], fg=self._c["fg"]).grid(row=0, column=0, sticky="ew")

        tk.Label(panel, text="Wk", font=HEADER_FONT, width=CELL_W,
                 bg=self._c["weekno_bg"], fg=self._c["weekno_fg"]
                 ).grid(row=1, column=0, sticky="nsew")
        for col, name in enumerate(WEEKDAY_ABBR, start=1):
            tk.Label(panel, text=name, font=HEADER_FONT, width=CELL_W,
                     bg=self._c["bg"], fg=self._c["header_fg"]
                     ).grid(row=1, column=col, sticky="nsew")

        weeks = month_grid(year, month)
        for row, (week, days) in enumerate(weeks, start=2):
            tk.Label(panel, text=f"{week:02d}", font=HEADER_FONT, width=CELL_W,
                     bg=self._c["weekno_bg"], fg=self._c["weekno_fg"]
                     ).grid(row=row, column=0, sticky="nsew")
            for col, day in enumerate(days, start=1):
                self._day_label(panel, day, month).grid(row=row, column=col, sticky="nsew")

        # Pad short months (4-5 rows) up to MAX_WEEK_ROWS so every panel is the
        # same height and the sidebar buttons stay put across month changes.
        for row in range(len(weeks) + 2, MAX_WEEK_ROWS + 2):
            tk.Label(panel, text="", font=HEADER_FONT, width=CELL_W,
                     bg=self._c["bg"]).grid(row=row, column=0, sticky="nsew")
            for col in range(1, 8):
                tk.Label(panel, text="", font=CELL_FONT, width=CELL_W,
                         bg=self._c["bg"]).grid(row=row, column=col, sticky="nsew")
        return panel

    def _day_label(self, parent: tk.Misc, day: date, month: int) -> tk.Label:
        if day == self._today:
            bg, fg = self._c["today_bg"], self._c["today_fg"]
        else:
            bg = self._c["bg"]
            fg = self._c["fg"] if day.month == month else self._c["muted"]
        return tk.Label(parent, text=str(day.day), font=CELL_FONT,
                        width=CELL_W, bg=bg, fg=fg)

    def _sidebar_button(self, parent: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(
            parent, text=text, font=TOOLBAR_BUTTON_FONT, width=2, bd=0, takefocus=False,
            bg=self._c["bg"], fg=self._c["fg"], activebackground=self._c["weekno_bg"],
            activeforeground=self._c["fg"], relief="flat", cursor="hand2",
            command=command,
        )

    def _mode_icon(self) -> str:
        # Popup mode shows maximize (popout), window mode shows minimize (popin).
        return "\U0001F5D7" if not self._window_mode else "\U0001F5D5"

    def _toggle_mode(self) -> None:
        self._set_window_mode(not self._window_mode)
        self._render()
        if not self._window_mode:
            self._place_near_tray()

    def _shift(self, delta: int) -> None:
        self._year, self._month = month_offset(self._year, self._month, delta)
        self._render()
        if not self._window_mode:
            self._place_near_tray()
        self._take_focus()

    def _on_double_click(self, event) -> None:
        if isinstance(event.widget, tk.Button):
            return
        # Deferred: _render() destroys the widget this event is still dispatching on.
        self.after_idle(self.go_to_today)

    def go_to_today(self) -> None:
        self._today = date.today()
        self._year, self._month = self._today.year, self._today.month
        self._render()
        if not self._window_mode:
            self._place_near_tray()
        self._take_focus()

    def _place_near_tray(self) -> None:
        self.update_idletasks()
        # Requested size tracks current content and avoids stale oversized geometry.
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        left, top, right, bottom = _work_area(self.winfo_screenwidth(), self.winfo_screenheight())
        margin = 8
        x = right - w - margin
        y = bottom - h - margin

        min_x = left + margin
        max_x = max(min_x, right - margin - 1)
        min_y = top + margin
        max_y = max(min_y, bottom - margin - 1)

        x = min(max(x, min_x), max_x)
        y = min(max(y, min_y), max_y)
        self.geometry(f"{w}x{h}+{x}+{y}")
