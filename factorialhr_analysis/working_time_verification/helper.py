"""Helper functions for working time verification."""

import dataclasses
import datetime
from collections.abc import Iterable, Sequence
from collections.abc import Set as AbstractSet

import factorialhr


def get_clock_in_and_clock_out(
    attendance: factorialhr.AttendanceShift,
) -> tuple[datetime.datetime | None, datetime.datetime | None]:
    """Get the clock in and clock out times from an attendance."""
    clock_in = (
        datetime.datetime.combine(attendance.date, attendance.clock_in.replace(second=0))
        if attendance.clock_in is not None
        else None
    )
    clock_out = (
        datetime.datetime.combine(attendance.date, attendance.clock_out.replace(second=0))
        if attendance.clock_out is not None
        else None
    )
    return clock_in, clock_out


def calculate_time_attended(attendances: Iterable[factorialhr.AttendanceShift]) -> datetime.timedelta:
    """Calculate the time attended.

    :param attendances: list of attendances
    :return: time attended
    """
    return datetime.timedelta(minutes=sum(shift.minutes for shift in attendances))


def calculate_break_time(attendances: Iterable[factorialhr.AttendanceShift]) -> datetime.timedelta:
    """Calculate the time between the specified attendances.

    :param attendances: list of attendances
    :return: time between attendances
    """
    attendances = sorted(attendances, key=lambda x: datetime.datetime.combine(x.date, x.clock_in))
    if not attendances:
        return datetime.timedelta(seconds=0)

    _, previous_clock_out = get_clock_in_and_clock_out(attendances[0])
    break_time = datetime.timedelta(seconds=0)
    for attendance in attendances[1:]:  # start at second index
        clock_in, clock_out = get_clock_in_and_clock_out(attendance)
        if attendance.clock_in is None or previous_clock_out is None:
            return datetime.timedelta(seconds=0)
        if clock_in <= previous_clock_out:
            # overlapping or contiguous attendances
            previous_clock_out = clock_out
            continue
        break_time += clock_in - previous_clock_out
        previous_clock_out = clock_out
    return break_time


@dataclasses.dataclass(frozen=True)
class Error:
    """Error found during verification."""

    reason: str
    attendances: Sequence[factorialhr.AttendanceShift]

    @property
    def days_affected(self) -> AbstractSet[datetime.date]:
        """Get the days affected."""
        return {attendance.date for attendance in self.attendances}

    @property
    def break_time(self) -> datetime.timedelta:
        """Get the break time."""
        return calculate_break_time(self.attendances)

    @property
    def time_attended(self) -> datetime.timedelta:
        """Get the time attended."""
        return calculate_time_attended(self.attendances)
