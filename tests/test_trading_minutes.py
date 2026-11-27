import pandas as pd
import pytest

from pandas_market_calendars import get_calendar
from tests.test_market_calendar import FakeBreakCalendar


@pytest.fixture(scope="module")
def nyse():
    return get_calendar("NYSE")


def test_trading_minutes_nyse_early_close_day_after_thanksgiving(nyse):
    assert nyse.trading_minutes("2026-11-27", "2026-11-27") == 210


def test_trading_minutes_nyse_full_week_of_five_sessions(nyse):
    assert nyse.trading_minutes("2026-11-16", "2026-11-20") == 5 * 390


def test_trading_minutes_nyse_thanksgiving_week_skips_holiday_and_counts_early_close(nyse):
    # Mon-Wed full, Thu holiday, Fri closes 13:00
    assert nyse.trading_minutes("2026-11-23", "2026-11-27") == 3 * 390 + 210


def test_trading_minutes_range_dates_outside_sessions_use_inner_sessions(nyse):
    # Saturday to Sunday around a full week is the same as the week itself
    assert nyse.trading_minutes("2026-11-14", "2026-11-22") == 5 * 390


def test_trading_minutes_weekend_without_session_is_zero(nyse):
    assert nyse.trading_minutes("2026-11-28", "2026-11-29") == 0


def test_trading_minutes_holiday_without_session_is_zero(nyse):
    assert nyse.trading_minutes("2026-11-26", "2026-11-26") == 0


def test_trading_minutes_ignores_time_of_day_in_dates(nyse):
    assert nyse.trading_minutes("2026-11-27 15:00", "2026-11-27 01:00") == 210


def test_trading_minutes_start_after_end_raises(nyse):
    with pytest.raises(ValueError, match="start_date"):
        nyse.trading_minutes("2026-11-20", "2026-11-16")


def test_trading_minutes_excludes_break():
    cal = FakeBreakCalendar()
    # 09:30-12:00 with a 10:00-11:00 break
    assert cal.trading_minutes("2016-12-28", "2016-12-28") == 90


def test_trading_minutes_late_open_after_break_start_counts_only_rest_of_break():
    cal = FakeBreakCalendar()
    # opens 10:20, break until 11:00, closes 12:00
    assert cal.trading_minutes("2016-12-29", "2016-12-29") == 60


def test_trading_minutes_early_close_inside_break():
    cal = FakeBreakCalendar()
    # opens 09:30, break from 10:00, closes 10:40 during the break
    assert cal.trading_minutes("2016-12-30", "2016-12-30") == 30


def test_trading_minutes_break_calendar_over_several_days():
    cal = FakeBreakCalendar()
    assert cal.trading_minutes("2016-12-28", "2016-12-30") == 90 + 60 + 30


def test_trading_minutes_hkex_lunch_break():
    hkex = get_calendar("HKEX")
    # 09:30-16:00 with a 12:00-13:00 lunch break
    assert hkex.trading_minutes("2026-11-16", "2026-11-16") == 330


def test_trading_minutes_hkex_half_day_before_break_has_no_break():
    hkex = get_calendar("HKEX")
    # Christmas Eve closes at 12:00, before the lunch break
    assert hkex.trading_minutes("2026-12-24", "2026-12-24") == 150


def test_next_open_after_early_close_is_next_monday(nyse):
    result = nyse.next_open(pd.Timestamp("2026-11-27 15:00", tz="America/New_York"))
    assert result == pd.Timestamp("2026-11-30 09:30", tz="America/New_York")


def test_next_open_keeps_time_zone_of_timestamp(nyse):
    result = nyse.next_open(pd.Timestamp("2026-11-27 15:00", tz="America/New_York"))
    assert str(result.tz) == "America/New_York"


def test_next_open_naive_timestamp_is_utc(nyse):
    # 13:00 UTC is 08:00 New York, before that day's open at 14:30 UTC
    result = nyse.next_open("2026-11-27 13:00")
    assert result == pd.Timestamp("2026-11-27 14:30", tz="UTC")
    assert str(result.tz) == "UTC"


def test_next_open_is_strictly_after_timestamp(nyse):
    result = nyse.next_open(pd.Timestamp("2026-11-27 09:30", tz="America/New_York"))
    assert result == pd.Timestamp("2026-11-30 09:30", tz="America/New_York")


def test_next_open_skips_holiday(nyse):
    result = nyse.next_open(pd.Timestamp("2026-11-25 17:00", tz="America/New_York"))
    assert result == pd.Timestamp("2026-11-27 09:30", tz="America/New_York")


def test_next_open_respects_late_open():
    cal = FakeBreakCalendar()
    result = cal.next_open(pd.Timestamp("2016-12-28 13:00", tz="America/New_York"))
    assert result == pd.Timestamp("2016-12-29 10:20", tz="America/New_York")
