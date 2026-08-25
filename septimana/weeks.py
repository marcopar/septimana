"""Date helpers.

The requested rule "the first week of the year is the week with at least 4 days"
is exactly the ISO 8601 definition, so everything here delegates to
``date.isocalendar()`` rather than re-deriving it.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import List, Tuple

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

# Monday-first, matching ISO 8601.
WEEKDAY_ABBR = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")

MonthRow = Tuple[int, List[date]]


def iso_week(day: date) -> int:
    """Return the ISO 8601 week number of *day*."""
    return day.isocalendar()[1]


def iso_year(day: date) -> int:
    """Return the ISO 8601 week-numbering year of *day*."""
    return day.isocalendar()[0]


def month_title(year: int, month: int) -> str:
    return f"{MONTH_NAMES[month - 1]} {year}"


def month_offset(year: int, month: int, delta: int) -> Tuple[int, int]:
    """Shift a (year, month) pair by *delta* months."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def month_grid(year: int, month: int) -> List[MonthRow]:
    """Return the calendar rows of a month as ``(week_number, [7 dates])``.

    Rows are padded with days from the adjacent months so every row has seven
    entries; the week number is taken from the row's Monday.
    """
    weeks = calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(year, month)
    return [(iso_week(row[0]), row) for row in weeks]
