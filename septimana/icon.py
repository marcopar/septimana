"""Renders the tray icon bitmap containing the week number."""

from __future__ import annotations

import ctypes
import threading
import winreg
from ctypes import wintypes

from PIL import Image, ImageDraw, ImageFont

# Matches the tray slot at 200% scaling; Windows downscales cleanly by 2 for 100%.
ICON_SIZE = 32

_FONT_CANDIDATES = ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")

LIGHT_TEXT = (255, 255, 255, 255)
DARK_TEXT = (0, 0, 0, 255)

_THEME_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
_REG_NOTIFY_CHANGE_LAST_SET = 0x00000004


def _theme_flag(name: str) -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _THEME_KEY) as key:
            return bool(winreg.QueryValueEx(key, name)[0])
    except OSError:
        return False


def taskbar_is_light() -> bool:
    """True when the taskbar uses the light system theme."""
    return _theme_flag("SystemUsesLightTheme")


def apps_are_light() -> bool:
    """True when app windows use the light theme; governs the popup colors."""
    return _theme_flag("AppsUseLightTheme")


def watch_theme(on_change) -> threading.Thread:
    """Call *on_change* (off the main thread) whenever the system theme changes."""

    def loop() -> None:
        while True:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _THEME_KEY) as key:
                    # Synchronous notify: blocks this thread until the key is written.
                    status = ctypes.windll.advapi32.RegNotifyChangeKeyValue(
                        wintypes.HANDLE(int(key)), False,
                        _REG_NOTIFY_CHANGE_LAST_SET, None, False,
                    )
                if status != 0:
                    return
            except OSError:
                return
            on_change()

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fitting_font(draw: ImageDraw.ImageDraw, text: str, box: int) -> ImageFont.ImageFont:
    for size in range(box, 5, -1):
        font = _load_font(size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        if right - left <= box and bottom - top <= box:
            return font
    return _load_font(6)


def render_icon(text: str) -> Image.Image:
    """Return a transparent RGBA icon with *text* centered on it."""
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    padding = 1
    font = _fitting_font(draw, text, ICON_SIZE - 2 * padding)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = (ICON_SIZE - (right - left)) / 2 - left
    y = (ICON_SIZE - (bottom - top)) / 2 - top

    # Solid contrasting text stays sharper than an outline once scaled to 16px.
    fill = DARK_TEXT if taskbar_is_light() else LIGHT_TEXT
    draw.text((x, y), text, font=font, fill=fill)
    return image
