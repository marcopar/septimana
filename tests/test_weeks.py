from datetime import date

import pytest

from septimana.weeks import iso_week, iso_year, month_grid, month_offset, month_title


@pytest.mark.parametrize(
    "day, expected_week, expected_year",
    [
        # 2021-01-01 is a Friday: its week has only 3 days in 2021, so it
        # belongs to week 53 of 2020.
        (date(2021, 1, 1), 53, 2020),
        # 2026-01-01 is a Thursday: the week has 4 days in 2026 -> week 1.
        (date(2026, 1, 1), 1, 2026),
        (date(2015, 12, 31), 53, 2015),
        # 2024-12-30 is a Monday whose week has 4 days in 2025 -> week 1/2025.
        (date(2024, 12, 30), 1, 2025),
        (date(2026, 8, 20), 34, 2026),
    ],
)
def test_iso_week(day, expected_week, expected_year):
    assert iso_week(day) == expected_week
    assert iso_year(day) == expected_year


def test_month_offset():
    assert month_offset(2026, 1, -1) == (2025, 12)
    assert month_offset(2026, 12, 1) == (2027, 1)
    assert month_offset(2026, 8, 0) == (2026, 8)
    assert month_offset(2026, 3, -14) == (2025, 1)


def test_month_title():
    assert month_title(2026, 8) == "August 2026"


def test_month_grid_shape():
    rows = month_grid(2026, 8)
    assert all(len(days) == 7 for _, days in rows)
    # Every row starts on a Monday.
    assert all(days[0].weekday() == 0 for _, days in rows)
    # All days of the month are present.
    covered = {d for _, days in rows for d in days if d.month == 8}
    assert len(covered) == 31


def test_month_grid_year_boundary():
    rows = month_grid(2026, 1)
    assert rows[0][0] == 1
    # December 2025 starts in week 49.
    assert month_grid(2025, 12)[0][0] == 49
