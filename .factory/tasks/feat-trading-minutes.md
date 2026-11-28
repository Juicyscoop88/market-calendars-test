# Trading minutes between two dates

The risk desk sets intraday limits per minute the market is open. Today every desk computes it by hand from `schedule()`, and they get early closes and breaks wrong.

Add `MarketCalendar.trading_minutes(start_date, end_date)`: the number of minutes the market is open from the first session on or after `start_date` to the last session on or before `end_date`, both included. Early closes and late opens count only the minutes the market is really open. Breaks (`break_start` to `break_end`, for example on some CME calendars) are not open minutes. A range with no session gives 0.

Also add `MarketCalendar.next_open(timestamp)`: the next `market_open` strictly after the timestamp (timezone aware, UTC if naive), taking late opens into account.

Examples:
- NYSE, 2026-11-27 (the day after Thanksgiving, closes 13:00): `trading_minutes("2026-11-27", "2026-11-27") == 210`.
- NYSE, a normal full week of five sessions: 5 * 390 = 1950.
- NYSE, `next_open("2026-11-27 15:00", tz America/New_York)` is Monday 2026-11-30 09:30 New York.

## Decisions

- **What should trading_minutes return when start_date is after end_date?** zero: return 0 for start > end, as the tester's test expects (decided by Juicyscoop88)
