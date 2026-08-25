"""Tray application wiring.

Tk must own the main thread, so the pystray icon runs on a daemon thread and
hands work back through ``root.after``.
"""

from __future__ import annotations

import threading
import tkinter as tk
from datetime import date, datetime, timedelta

import pystray

from .calendar_popup import CalendarPopup
from .icon import render_icon, watch_theme
from .weeks import iso_week

# Ignore an icon click that arrives right after a focus-out closed the popup,
# otherwise the same click would immediately reopen it.
_REOPEN_GUARD_MS = 300


def _icon_text(week: int) -> str:
    return f"{week:02d}"


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self._popup: CalendarPopup | None = None
        self._closed_at = 0

        today = date.today()
        self.icon = pystray.Icon(
            "septimana",
            # Built before the icon thread starts, so the tray never shows a placeholder.
            icon=render_icon(_icon_text(iso_week(today))),
            title=self._tooltip(today),
            menu=pystray.Menu(
                pystray.MenuItem("Open", self._on_activate, default=True, visible=False),
                pystray.MenuItem("Exit", self._on_exit),
            ),
        )

    # -- tray callbacks (background thread) --------------------------------

    def _on_activate(self, _icon=None, _item=None) -> None:
        self.root.after(0, self.toggle_popup)

    def _on_exit(self, _icon=None, _item=None) -> None:
        self.root.after(0, self.shutdown)

    # -- Tk thread ---------------------------------------------------------

    def toggle_popup(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.present()
            return
        if self.root.tk.call("clock", "milliseconds") - self._closed_at < _REOPEN_GUARD_MS:
            return
        self._popup = CalendarPopup(self.root, on_close=self._on_popup_closed)
        self._popup.present()

    def _on_popup_closed(self) -> None:
        self._popup = None
        self._closed_at = self.root.tk.call("clock", "milliseconds")

    def refresh(self) -> None:
        today = date.today()
        self.icon.icon = render_icon(_icon_text(iso_week(today)))
        self.icon.title = self._tooltip(today)

    def _on_theme_changed(self) -> None:
        try:
            self.root.after(0, self.refresh)
        except RuntimeError:
            pass  # Tk is already gone; nothing left to redraw.

    @staticmethod
    def _tooltip(today: date) -> str:
        return f"Week {iso_week(today)} \u2014 {today:%d %b %Y}"

    def _daily_refresh(self) -> None:
        self.refresh()
        self._schedule_next_refresh()

    def _schedule_next_refresh(self) -> None:
        now = datetime.now()
        midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        delay_ms = int((midnight - now).total_seconds() * 1000) + 1000
        self.root.after(delay_ms, self._daily_refresh)

    def shutdown(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
        self.icon.stop()
        self.root.quit()

    def run(self) -> None:
        threading.Thread(target=self.icon.run, daemon=True).start()
        watch_theme(self._on_theme_changed)
        self._schedule_next_refresh()
        self.root.mainloop()
        self.root.destroy()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
