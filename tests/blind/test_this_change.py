# Four Eyes: written by the gate's tester, who never saw the code, from the spec 4b8830902837
from datetime import time
from decimal import Decimal

import pandas as pd
import pytest

import pandas_market_calendars as mcal
from pandas_market_calendars.market_calendar import MarketCalendar


@pytest.fixture
def nyse():
    return mcal.get_calendar("NYSE")


@pytest.fixture
def xhkg():
    return mcal.get_calendar("XHKG")


def test_early_close_day(nyse):
    """Example: NYSE 2026-11-27 closes 13:00 -> 210."""
    assert nyse.trading_minutes("2026-11-27", "2026-11-27") == 210


def test_full_week(nyse):
    """Example: a normal full week is 5 * 390."""
    assert nyse.trading_minutes("2026-11-02", "2026-11-06") == 1950


def test_returns_int(nyse):
    """Docstring: number of open minutes as an int."""
    r = nyse.trading_minutes("2026-11-02", "2026-11-02")
    assert isinstance(r, int) and r == 390


def test_thanksgiving_week(nyse):
    """Example: closed Thursday, early Friday -> 1380."""
    assert nyse.trading_minutes("2026-11-23", "2026-11-27") == 1380


def test_hk_break_subtracted(xhkg):
    """Example: XHKG 2026-11-23 09:30-16:00 minus lunch -> 330."""
    assert xhkg.trading_minutes("2026-11-23", "2026-11-23") == 330


def test_hk_early_close_before_break(xhkg):
    """Example: XHKG 2026-12-24 closes 12:00, break takes nothing -> 150."""
    assert xhkg.trading_minutes("2026-12-24", "2026-12-24") == 150


def test_no_session_range_is_zero(nyse):
    """A range with no session gives 0 (weekend; holiday)."""
    assert nyse.trading_minutes("2026-11-28", "2026-11-29") == 0
    assert nyse.trading_minutes("2026-11-26", "2026-11-26") == 0


def test_start_after_end_is_zero(nyse):
    """Decision: start_date after end_date returns 0."""
    assert nyse.trading_minutes("2026-11-24", "2026-11-23") == 0


def test_range_edges_snap_to_sessions(nyse):
    """First session on or after start, last on or before end: weekend edges."""
    assert nyse.trading_minutes("2026-11-21", "2026-11-22") == 0
    assert nyse.trading_minutes("2026-11-21", "2026-11-24") == 780


def test_time_and_tz_ignored(nyse):
    """Decision: times/time zones in dates are ignored -> 780."""
    assert nyse.trading_minutes("2026-11-23 15:00", "2026-11-24") == 780
    assert nyse.trading_minutes("2026-11-23", "2026-11-24 03:00") == 780
    assert (
        nyse.trading_minutes(
            pd.Timestamp("2026-11-23 23:30", tz="America/New_York"),
            pd.Timestamp("2026-11-24 00:10", tz="Asia/Tokyo"),
        )
        == 780
    )


def test_zero_length_break_counts_full():
    """Decision: CME_Equity break_start == break_end is no break; sessions count in full."""
    cal = mcal.get_calendar("CME_Equity")
    sched = cal.schedule("2026-11-17", "2026-11-17")
    full = int((sched["market_close"] - sched["market_open"]).iloc[0].total_seconds() // 60)
    assert cal.trading_minutes("2026-11-17", "2026-11-17") == full


def test_break_needs_both_ends(xhkg):
    """Decision: with only break_start defined, the break is ignored."""
    xhkg.remove_time("break_end")
    assert xhkg.trading_minutes("2026-11-23", "2026-11-23") == 390


def test_next_open_after_early_close_friday(nyse):
    """Example: Friday 15:00 -> Monday 09:30 New York."""
    r = nyse.next_open(pd.Timestamp("2026-11-27 15:00", tz="America/New_York"))
    assert r == pd.Timestamp("2026-11-30 09:30", tz="America/New_York")


def test_next_open_strictly_after(nyse):
    """Example: exactly at an open gives the next day's open."""
    r = nyse.next_open(pd.Timestamp("2026-11-30 09:30", tz="America/New_York"))
    assert r == pd.Timestamp("2026-12-01 09:30", tz="America/New_York")


def test_next_open_one_minute_before_open(nyse):
    """Boundary: one minute before the open gives that open."""
    r = nyse.next_open(pd.Timestamp("2026-11-30 09:29", tz="America/New_York"))
    assert r == pd.Timestamp("2026-11-30 09:30", tz="America/New_York")


def test_next_open_naive_is_utc_and_result_in_utc(nyse):
    """Naive timestamps are UTC and the result is in UTC."""
    r = nyse.next_open("2026-11-30 12:00")
    assert r == pd.Timestamp("2026-11-30 14:30", tz="UTC")
    assert str(r.tz) == "UTC"


def test_next_open_result_keeps_input_timezone(nyse):
    """Docstring: result is in the time zone of the timestamp."""
    r = nyse.next_open(pd.Timestamp("2026-11-30 09:30", tz="America/New_York"))
    assert str(r.tz) == "America/New_York"


def test_next_open_cme_evening_before():
    """Example: CMES Sunday 12:00 Chicago -> Sunday 17:00 Chicago."""
    cal = mcal.get_calendar("CMES")
    r = cal.next_open(pd.Timestamp("2026-11-29 12:00", tz="America/Chicago"))
    assert r == pd.Timestamp("2026-11-29 17:00", tz="America/Chicago")


class _LateOpenNYSE(type(mcal.get_calendar("NYSE"))):
    aliases = ["_LATE_OPEN_TEST"]

    @property
    def name(self):
        return "_LateOpenTest"

    @property
    def special_opens_adhoc(self):
        return [(time(11, 0), pd.DatetimeIndex(["2026-12-01"]))]


def test_late_open_minutes_and_next_open():
    """Late opens count only open minutes and next_open respects them (read-only array fix)."""
    cal = _LateOpenNYSE()
    assert cal.trading_minutes("2026-12-01", "2026-12-01") == 300
    r = cal.next_open(pd.Timestamp("2026-11-30 12:00", tz="America/New_York"))
    assert r == pd.Timestamp("2026-12-01 11:00", tz="America/New_York")


def test_open_next_open_no_session_in_ten_years_raises(nyse):
    """Decision: ValueError when no open within ten years (hard to provoke on NYSE; far-future timestamp)."""
    with pytest.raises(ValueError):
        nyse.next_open(pd.Timestamp("2500-01-01", tz="UTC"))
