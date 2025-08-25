"""Unit tests for working_time_verification module."""

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from factorialhr_analysis.working_time_verification import helper, verification


@dataclass(frozen=True)
class FakeShift:
    """Minimal stand-in for factorialhr.AttendanceShift for testing."""

    date: dt.date
    clock_in: dt.time | None
    clock_out: dt.time | None
    workable: bool = True
    minutes: int = 0
    id: int = 0

    def __post_init__(self) -> None:
        """Populate minutes from clock_in/clock_out when not explicitly provided."""
        # dataclass with frozen=True can't mutate; use object.__setattr__
        if self.minutes == 0 and self.clock_in and self.clock_out:
            cin = dt.datetime.combine(self.date, self.clock_in)
            cout = dt.datetime.combine(self.date, self.clock_out)
            m = max(0, int((cout - cin).total_seconds() // 60))
            object.__setattr__(self, 'minutes', m)


@pytest.mark.parametrize(
    ('clock_in', 'clock_out', 'exp_in', 'exp_out'),
    [
        (
            dt.time(9, 0, 30),
            dt.time(17, 0, 45),
            dt.datetime.combine(dt.date(2024, 1, 1), dt.time(9, 0)),
            dt.datetime.combine(dt.date(2024, 1, 1), dt.time(17, 0)),
        ),
        (None, dt.time(12, 0), None, dt.datetime.combine(dt.date(2024, 1, 1), dt.time(12, 0))),
        (dt.time(8, 0), None, dt.datetime.combine(dt.date(2024, 1, 1), dt.time(8, 0)), None),
        (None, None, None, None),
    ],
)
def test_get_clock_in_and_clock_out(
    clock_in: dt.time | None, clock_out: dt.time | None, exp_in: dt.datetime | None, exp_out: dt.datetime | None
) -> None:
    """Ensure helper returns expected naive datetimes (seconds truncated)."""
    shift = FakeShift(date=dt.date(2024, 1, 1), clock_in=clock_in, clock_out=clock_out)
    got_in, got_out = helper.get_clock_in_and_clock_out(shift)  # type: ignore[arg-type]
    assert got_in == exp_in
    assert got_out == exp_out


@pytest.mark.parametrize(
    ('minutes_list', 'expected'),
    [([60], dt.timedelta(hours=1)), ([30, 45], dt.timedelta(minutes=75)), ([], dt.timedelta(0))],
)
def test_calculate_time_attended(minutes_list: list[int], expected: dt.timedelta) -> None:
    """Sum minutes across shifts to a timedelta."""
    base = dt.date(2024, 1, 1)
    shifts = [FakeShift(base, dt.time(9, 0), dt.time(10, 0), minutes=m) for m in minutes_list]
    assert helper.calculate_time_attended(shifts) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ('shifts', 'expected'),
    [
        (
            [
                FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(12, 0)),
                FakeShift(dt.date(2024, 1, 1), dt.time(13, 0), dt.time(17, 0)),
            ],
            dt.timedelta(hours=1),
        ),
        (
            [
                FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(12, 0)),
                FakeShift(dt.date(2024, 1, 1), dt.time(11, 0), dt.time(14, 0)),
            ],
            dt.timedelta(0),
        ),
        (
            [
                FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(12, 0)),
                FakeShift(dt.date(2024, 1, 1), dt.time(12, 0), dt.time(17, 0)),
            ],
            dt.timedelta(0),
        ),
        (
            [
                FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(10, 0)),
                FakeShift(dt.date(2024, 1, 1), dt.time(11, 0), dt.time(12, 0)),
                FakeShift(dt.date(2024, 1, 1), dt.time(13, 0), dt.time(14, 0)),
            ],
            dt.timedelta(hours=2),
        ),
    ],
)
def test_calculate_break_time(shifts: Sequence[FakeShift], expected: dt.timedelta) -> None:
    """Compute total gap between non-overlapping sequential shifts."""
    assert helper.calculate_break_time(shifts) == expected  # type: ignore[arg-type]


def test_calculate_break_time_empty() -> None:
    """Empty attendances should yield zero break time."""
    assert helper.calculate_break_time([]) == dt.timedelta(0)  # type: ignore[arg-type]


def test_calculate_break_time_missing_first_clock_out_returns_zero() -> None:
    """If the first shift has no clock_out, break computation returns zero early."""
    shifts = [
        FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), None),
        FakeShift(dt.date(2024, 1, 1), dt.time(10, 0), dt.time(11, 0)),
    ]
    assert helper.calculate_break_time(shifts) == dt.timedelta(0)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ('attendances', 'exp_days', 'exp_break', 'exp_time'),
    [
        (
            [
                FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(10, 0)),
                FakeShift(dt.date(2024, 1, 1), dt.time(11, 0), dt.time(12, 0)),
            ],
            {dt.date(2024, 1, 1)},
            dt.timedelta(hours=1),
            dt.timedelta(hours=2),
        ),
        (
            [
                FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(10, 0)),
                FakeShift(dt.date(2024, 1, 2), dt.time(11, 0), dt.time(12, 0)),
            ],
            {dt.date(2024, 1, 1), dt.date(2024, 1, 2)},
            dt.timedelta(days=1, hours=1),
            dt.timedelta(hours=2),
        ),
    ],
)
def test_error_properties(
    attendances: Sequence[FakeShift], exp_days: set[dt.date], exp_break: dt.timedelta, exp_time: dt.timedelta
) -> None:
    """Validate Error aggregates derived properties correctly."""
    err = helper.Error('test', attendances)
    assert err.days_affected == exp_days
    assert err.break_time == exp_break
    assert err.time_attended == exp_time


@pytest.mark.parametrize(
    ('shift', 'expected_reason'),
    [
        (FakeShift(dt.date(2024, 1, 1), None, dt.time(12, 0)), 'no clock in time provided'),
        (FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), None), 'no clock out time provided'),
        (FakeShift(dt.date(2024, 1, 1), dt.time(10, 0), dt.time(9, 0)), 'Clocked out earlier or at the same time'),
        (FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(9, 1)), None),
    ],
)
def test_validate_clock_times(shift: FakeShift, expected_reason: str | None) -> None:
    """Validate basic structure and ordering of clock times."""
    res = verification.validate_clock_times(shift)  # type: ignore[arg-type]
    if expected_reason is None:
        assert res is None
    else:
        assert isinstance(res, helper.Error)
        assert expected_reason in res.reason


@pytest.mark.parametrize(
    ('shift', 'tolerance', 'expected_flags'),
    [
        (
            FakeShift(dt.date(2024, 1, 1), dt.time(5, 30), dt.time(14, 0)),
            dt.timedelta(minutes=0),
            (True, False),
        ),
        (
            FakeShift(dt.date(2024, 1, 1), dt.time(5, 50), dt.time(14, 0)),
            dt.timedelta(minutes=15),
            (False, False),
        ),
        (
            FakeShift(dt.date(2024, 1, 1), dt.time(14, 0), dt.time(22, 30)),
            dt.timedelta(minutes=10),
            (False, True),
        ),
        (
            FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(17, 0)),
            dt.timedelta(minutes=0),
            (False, False),
        ),
    ],
)
def test_check_attendance_time(shift: FakeShift, tolerance: dt.timedelta, expected_flags: tuple[bool, bool]) -> None:
    """Detect early clock-in and late clock-out events respecting tolerance."""
    errs = list(verification.check_attendance_time(shift, tolerance))  # type: ignore[arg-type]
    reasons = [e.reason for e in errs]
    exp_early, exp_late = expected_flags
    assert any('Clocked in' in r for r in reasons) == exp_early
    assert any('Clocked out' in r for r in reasons) == exp_late


@pytest.mark.parametrize(
    ('existing', 'new_clock_in', 'expected'),
    [
        ([], dt.datetime.combine(dt.date(2024, 1, 1), dt.time(10, 0)), dt.timedelta(0)),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(10, 0))],
            dt.datetime.combine(dt.date(2024, 1, 1), dt.time(11, 0)),
            dt.timedelta(hours=1),
        ),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(10, 0))],
            dt.datetime.combine(dt.date(2024, 1, 1), dt.time(9, 30)),
            dt.timedelta(0),
        ),
    ],
)
def test_calculate_break(existing: list[FakeShift], new_clock_in: dt.datetime, expected: dt.timedelta) -> None:
    """Calculate break between last shift and next clock-in."""
    assert verification.calculate_break(existing, new_clock_in) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ('attendances', 'tolerance', 'expected'),
    [
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(15, 1))],
            dt.timedelta(0),
            ('more than 6 hours', False),
        ),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(8, 0), dt.time(17, 1))],
            dt.timedelta(0),
            ('more than 9 hours', False),
        ),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(7, 0), dt.time(17, 1))],
            dt.timedelta(0),
            ('more than 10 hours', True),
        ),
        (
            [
                FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(12, 0)),
                FakeShift(dt.date(2024, 1, 1), dt.time(12, 45), dt.time(17, 0)),
            ],
            dt.timedelta(0),
            (None, False),
        ),
    ],
)
def test_check_breaks_and_reset(
    attendances: Sequence[FakeShift], tolerance: dt.timedelta, expected: tuple[str | None, bool]
) -> None:
    """Check cumulative break requirements and whether to reset accumulation."""
    exp_reason_substr, exp_reset = expected
    error, reset = verification.check_breaks_and_reset(attendances, tolerance)  # type: ignore[arg-type]
    if exp_reason_substr is None:
        assert error is None
        assert reset is False
    else:
        assert isinstance(error, helper.Error)
        assert exp_reason_substr in error.reason
        assert reset is exp_reset


@pytest.mark.parametrize(
    ('attendances', 'tolerance', 'exp_reasons_contains'),
    [
        (
            [FakeShift(dt.date(2024, 1, 1), None, dt.time(12, 0))],
            dt.timedelta(0),
            ['no clock in'],
        ),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(5, 30), dt.time(12, 0))],
            dt.timedelta(0),
            ['Clocked in'],
        ),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(14, 0), dt.time(22, 30))],
            dt.timedelta(minutes=0),
            ['Clocked out'],
        ),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(15, 1))],
            dt.timedelta(0),
            ['more than 6 hours'],
        ),
        (
            [FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), None, workable=False)],
            dt.timedelta(0),
            ['no clock out'],
        ),
    ],
)
def test_get_error_end_to_end(
    attendances: Sequence[FakeShift], tolerance: dt.timedelta, exp_reasons_contains: Sequence[str]
) -> None:
    """End-to-end verification across common scenarios."""
    reasons = [e.reason for e in verification.get_error(attendances, tolerance)]  # type: ignore[arg-type]
    for needle in exp_reasons_contains:
        assert any(needle in r for r in reasons)


def test_get_error_skips_non_workable_with_valid_times() -> None:
    """Non-workable attendances with valid times should be skipped with no errors."""
    shifts = [FakeShift(dt.date(2024, 1, 1), dt.time(9, 0), dt.time(10, 0), workable=False)]
    errors = list(verification.get_error(shifts, dt.timedelta(0)))  # type: ignore[arg-type]
    assert errors == []


def test_get_error_resets_on_eleven_hour_break() -> None:
    """A break >= 11 hours should reset accumulation between shifts."""
    shifts = [
        FakeShift(dt.date(2024, 1, 1), dt.time(8, 0), dt.time(9, 0)),
        FakeShift(dt.date(2024, 1, 1), dt.time(21, 30), dt.time(21, 45)),  # 12.5h break
    ]
    reasons = [e.reason for e in verification.get_error(shifts, dt.timedelta(0))]  # type: ignore[arg-type]
    # No break-violation errors expected; early/late bounds are satisfied
    assert all('more than' not in r for r in reasons)


def test_get_error_triggers_reset_on_ten_hour_violation() -> None:
    """Working more than 10 hours with <11h break should yield an error and reset accumulation."""
    shifts = [FakeShift(dt.date(2024, 1, 1), dt.time(7, 0), dt.time(17, 1))]  # >10h
    errors = list(verification.get_error(shifts, dt.timedelta(0)))  # type: ignore[arg-type]
    assert any('more than 10 hours' in e.reason for e in errors)
