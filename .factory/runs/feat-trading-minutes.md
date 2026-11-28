## Four Eyes gate

⛔ **Blocked.** Tier **money**.

### What blocks it

- independent tests caught 0 of 17 injected faults, tier money needs 80%

### Decide only these

Reply with one line per card, for example `/decide 1 keep`, or `/decide 1 <your own answer>`. Each answer becomes a blind test first, then code.

**1. Is the clamped-break rule right: only the part of the break inside [open, close] is subtracted, and a day with NaT break times loses nothing?**  
`pandas_market_calendars/market_calendar.py:1097`: The break-overlap arithmetic (clamping break to the session, subtracting from open time) had 8 surviving faults (M11-M15, M7, M6), so only the author's own tests vouch for money-relevant minute counts on break calendars.
- `/decide 1 keep`: subtract only the in-session overlap of the break
- `/decide 1 strict`: subtract the full break_start to break_end whenever both exist
- `/decide 1 other`: tell me the rule for days where the session ends before the break or opens after it

**2. Should trading_minutes subtract breaks only when both break_start and break_end are defined for the calendar?**  
`pandas_market_calendars/market_calendar.py:1079`: The has_break condition (`in` flipped to `not in`) survived independent tests, so whether break calendars take the break path at all is unverified. Calendars with only one of break_start or break_end are treated as having no break.
- `/decide 2 keep`: both required, otherwise ignore the break
- `/decide 2 either`: use the break path if either is defined and treat the missing one as the session edge
- `/decide 2 raise`: raise an error for a half-defined break

**3. If no open is found within the search windows, should next_open raise ValueError?**  
`pandas_market_calendars/market_calendar.py:1119`: next_open's window search and the final error (M25-M28 survived, including a removed `raise` and a flipped `not`) have no independent test. Special-time handling and the ten-year limit are unverified, and a CME-style calendar whose open is the previous evening is untested.
- `/decide 3 keep`: raise ValueError after ten years
- `/decide 3 none`: return NaT
- `/decide 3 shorter`: raise after a shorter limit such as one year

> Adds trading_minutes and next_open, and patches _apply_special_times to copy read-only arrays. Most of the break and clipping arithmetic has no independent test (15 of 17 injected faults were caught only by the author's tests, 0 by tester or protected tests), so a person must judge three places.

### Tests

1638 tests ran, 0 failed.

### Do the tests prove anything?

17 small faults were injected into the changed lines, one at a time (11 more changed no behavior, see below).

| Tests | Written by | Caught | Counts |
|---|---|---|---|
| author | whoever wrote the code | 15 of 17 | no, nobody checks their own work |
| tester | the tester, who never saw the code | 0 of 17 | yes |
| protected | people own them | 0 of 17 | yes |
| **tester + protected** | | **0 of 17** (0%, needs 80%) | |

<details><summary>Faults no independent test caught</summary>

- M1 `pandas_market_calendars/market_calendar.py:1075` `>` became `>=`
- M3 `pandas_market_calendars/market_calendar.py:1079` `in` became `not in`
- M4 `pandas_market_calendars/market_calendar.py:1079` `in` became `not in`
- M6 `pandas_market_calendars/market_calendar.py:1085` `0` became `1`
- M7 `pandas_market_calendars/market_calendar.py:1088` `-` became `+`
- M11 `pandas_market_calendars/market_calendar.py:1097` `-` became `+`
- M12 `pandas_market_calendars/market_calendar.py:1097` `0` became `1`
- M13 `pandas_market_calendars/market_calendar.py:1098` `0` became `1`
- M14 `pandas_market_calendars/market_calendar.py:1098` `-` became `+`
- M15 `pandas_market_calendars/market_calendar.py:1100` `1` became `2`
- M18 `pandas_market_calendars/market_calendar.py:1110` `is` became `is not`
- M20 `pandas_market_calendars/market_calendar.py:1115` `-` became `+`
- M24 `pandas_market_calendars/market_calendar.py:1117` `+` became `-`
- M25 `pandas_market_calendars/market_calendar.py:1119` `>` became `>=`
- M26 `pandas_market_calendars/market_calendar.py:1120` a `not` was removed
- M27 `pandas_market_calendars/market_calendar.py:1121` `0` became `1`
- M28 `pandas_market_calendars/market_calendar.py:1123` a `raise` was removed (a guard that no longer guards)

</details>

<details><summary>Faults judged equivalent by the reviewer (not counted)</summary>

- M2 `pandas_market_calendars/market_calendar.py:1076` `0` became `1`: The result is 0 when start is after end. The only way to reach the replaced constant is the guard's own return value, and the faulty version returns 1 there. So it is not equivalent: a test with start after end must expect exactly 0, not 1.
- M5 `pandas_market_calendars/market_calendar.py:1079` `and` became `or`: A calendar defines break_start and break_end together or not at all. So 'both present' and 'either present' give the same answer for every real calendar.
- M8 `pandas_market_calendars/market_calendar.py:1088` `0` became `1`: The lower bound is only reached for zero or negative lengths, and the change makes it 1 nanosecond instead of 0. The total is floored to whole minutes, so no input changes the result.
- M9 `pandas_market_calendars/market_calendar.py:1095` `>` became `>=`: When the break start equals the session open, the replacement value is that same open. The result is identical either way.
- M10 `pandas_market_calendars/market_calendar.py:1096` `<` became `<=`: When the break end equals the session close, the replacement value is that same close. The result is identical either way.
- M16 `pandas_market_calendars/market_calendar.py:1100` `//` became `/`: Behaviour differs only in the type: a float vs integer division. A total of whole minutes is equal either way in value, so only a type check on the result (integer) can tell them apart. Test that the result is an integer.
- M17 `pandas_market_calendars/market_calendar.py:1100` the call to `int()` was removed: The Timedelta floor division already returns a plain integer, so wrapping it in int() changes neither the value nor the type.
- M19 `pandas_market_calendars/market_calendar.py:1115` `7` became `8`: The search only starts a few days earlier or later than needed and then keeps opens after the timestamp. A one-day change in the lookback gives the same first open.
- M21 `pandas_market_calendars/market_calendar.py:1116` `31` became `32`: The first search window is widened to larger windows when nothing is found, so one more day in its length changes the result only if an open lies exactly at the edge, which the wider fallback windows cover anyway. No input gives a different answer.
- M22 `pandas_market_calendars/market_calendar.py:1116` `366` became `367`: The second window is only used when the first has no open, and then it is one day longer. An open falling exactly on that extra day would be found by the third window anyway, with the same value, so the outcome is identical.
- M23 `pandas_market_calendars/market_calendar.py:1116` `3660` became `3661`: The last window is one day longer, and only changes whether an error is raised for an open exactly ten years out. This is not realistically testable on real calendars.

</details>

### Reviewer findings

- **warn** `pandas_market_calendars/market_calendar.py:802`: The change to _apply_special_times (x.copy() inside adjust_opens and adjust_closes) is outside the task and affects every schedule() call using special times. The gate's 1638 passing tests cover it, but progress.md still lists test_next_open_respects_late_open as failing in this function. Confirm it passes.
- **warn** `tests/test_trading_minutes.py:22`: The only start > end test uses NYSE with two full sessions, so the guard at line 1075 (`>` vs `>=`, M1) is unpinned for start == end on a day that has a session. A single-day range returning 0 would be wrong, and the existing early-close test covers it only through the author's own test.

### Provenance

- change: `976e2be53e..bbf973b3ad`, 4 files
- requested by: Juicyscoop88; approver must be someone else
- agents that checked it: tester (sonnet, $0.014), author (sonnet, $0.079), author (sonnet, $0.078), reviewer (sonnet, $0.042), tester (sonnet, $0.019), reviewer (sonnet, $0.063), tester (sonnet, $0.015), reviewer (sonnet, $0.055), tester (sonnet, $0.016), tester (sonnet, $0.015), reviewer (sonnet, $0.030); total $0.425
- gate run: 2026-11-27 18:20 UTC

<!-- four-eyes-stats {"passed": false, "tier": "money", "files": 4, "tests_run": 1638, "failures": 0, "preexisting": 0, "mutants": 17, "caught": 0, "cards": 3, "blind_written": false, "cost_usd": 0.425} -->

<!-- four-eyes-cards [{"where": "pandas_market_calendars/market_calendar.py:1097", "why": "The break-overlap arithmetic (clamping break to the session, subtracting from open time) had 8 surviving faults (M11-M15, M7, M6), so only the author's own tests vouch for money-relevant minute counts on break calendars.", "question": "Is the clamped-break rule right: only the part of the break inside [open, close] is subtracted, and a day with NaT break times loses nothing?", "options": ["keep: subtract only the in-session overlap of the break", "strict: subtract the full break_start to break_end whenever both exist", "other: tell me the rule for days where the session ends before the break or opens after it"], "id": "1"}, {"where": "pandas_market_calendars/market_calendar.py:1079", "why": "The has_break condition (`in` flipped to `not in`) survived independent tests, so whether break calendars take the break path at all is unverified. Calendars with only one of break_start or break_end are treated as having no break.", "question": "Should trading_minutes subtract breaks only when both break_start and break_end are defined for the calendar?", "options": ["keep: both required, otherwise ignore the break", "either: use the break path if either is defined and treat the missing one as the session edge", "raise: raise an error for a half-defined break"], "id": "2"}, {"where": "pandas_market_calendars/market_calendar.py:1119", "why": "next_open's window search and the final error (M25-M28 survived, including a removed `raise` and a flipped `not`) have no independent test. Special-time handling and the ten-year limit are unverified, and a CME-style calendar whose open is the previous evening is untested.", "question": "If no open is found within the search windows, should next_open raise ValueError?", "options": ["keep: raise ValueError after ten years", "none: return NaT", "shorter: raise after a shorter limit such as one year"], "id": "3"}] -->
