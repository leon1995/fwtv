"""Module to verify working time regulations based on attendances."""

import datetime
from collections.abc import Iterable, Iterator

import factorialhr

from factorialhr_analysis.working_time_verification import helper

HOURS_6 = datetime.timedelta(hours=6)
HOURS_9 = datetime.timedelta(hours=9)
HOURS_10 = datetime.timedelta(hours=10)
HOURS_11 = datetime.timedelta(hours=11)
MINUTES_30 = datetime.timedelta(minutes=30)
MINUTES_45 = datetime.timedelta(minutes=45)

SIX_AM = datetime.time(hour=6, minute=0, second=0)
TEN_PM = datetime.time(hour=22, minute=0, second=0)


def validate_clock_times(attendance: factorialhr.AttendanceShift) -> helper.Error | None:
    """Validate that clock-in and clock-out times are present and logical."""
    clock_in, clock_out = helper.get_clock_in_and_clock_out(attendance)
    if clock_in is None:
        return helper.Error(f'no clock in time provided for attendance with id {attendance.id}', [attendance])
    if clock_out is None:
        return helper.Error(f'no clock out time provided for clock in time {attendance.clock_in}', [attendance])
    if clock_out <= clock_in:
        return helper.Error('Clocked out earlier or at the same time as clocked in', [attendance])
    return None


def check_attendance_time(attendance: factorialhr.AttendanceShift, tolerance: datetime.timedelta):
    """Check for clock-in before 6 AM and clock-out after 10 PM, respecting tolerance."""
    clock_in, clock_out = helper.get_clock_in_and_clock_out(attendance)
    six_am = datetime.datetime.combine(clock_in.date(), SIX_AM)
    if clock_in < six_am - tolerance:
        yield helper.Error(f'Clocked in after {SIX_AM} at {clock_in.time()}', [attendance])
    ten_pm = datetime.datetime.combine(clock_out.date(), TEN_PM)
    if clock_out > ten_pm + tolerance:
        yield helper.Error(f'Clocked out after {TEN_PM} at {clock_out.time()}', [attendance])


def calculate_break(
    current_attendances: list[factorialhr.AttendanceShift], clock_in: datetime.datetime
) -> datetime.timedelta:
    """Calculate the break time between the last attendance and the current clock-in."""
    if current_attendances:
        _, last_attendance_clock_out = helper.get_clock_in_and_clock_out(current_attendances[-1])
        if last_attendance_clock_out is not None and clock_in > last_attendance_clock_out:
            return clock_in - last_attendance_clock_out
    return datetime.timedelta(seconds=0)


def check_breaks_and_reset(
    current_attendances: list[factorialhr.AttendanceShift], tolerance: datetime.timedelta
) -> tuple[helper.Error | None, bool]:
    """Check for legal break durations and determines if attendances should be reset."""
    cumulated_time_attended = helper.calculate_time_attended(current_attendances)
    cumulated_break_time = helper.calculate_break_time(current_attendances)
    reason = None
    reset = False
    if cumulated_time_attended > HOURS_6 + tolerance and cumulated_break_time < MINUTES_30:
        reason = 'Attended more than 6 hours without a cumulated break of 30 min'
    if cumulated_time_attended > HOURS_9 + tolerance and cumulated_break_time < MINUTES_45:
        reason = 'Attended more than 9 hours without a cumulated break of 45 min'
    if cumulated_time_attended > HOURS_10 + tolerance and cumulated_break_time < HOURS_11:
        reason = 'Attended more than 10 hours without a single break of 11 hours'
        reset = True
    return helper.Error(reason=reason, attendances=current_attendances[:]) if reason else None, reset


def get_error(
    attendances: Iterable[factorialhr.AttendanceShift],
    tolerance: datetime.timedelta | None = None,
) -> Iterator[helper.Error]:
    """Verification function.

    Iterates over attendances and yields any errors found. Splits logic into smaller helper functions for clarity and
    maintainability.
    """
    tolerance = tolerance or datetime.timedelta()
    current_attendances: list[factorialhr.AttendanceShift] = []
    for attendance in attendances:
        # Validate clock-in/clock-out times
        error = validate_clock_times(attendance)
        if error:
            yield error
            continue
        if not attendance.workable:
            continue  # Declared as a break, skip
        # Ensure correct order
        current_attendances.sort(key=lambda x: (x.clock_out, x.clock_out))
        # Check for early/late attendance
        yield from check_attendance_time(attendance, tolerance)
        clock_in, clock_out = helper.get_clock_in_and_clock_out(attendance)
        # Calculate break time and reset attendances if needed
        break_time = calculate_break(current_attendances, clock_in)
        if break_time >= HOURS_11:
            current_attendances = [attendance]
        else:
            current_attendances.append(attendance)
        # Check for legal break durations and reset if necessary
        error, reset = check_breaks_and_reset(current_attendances, tolerance)
        if error:
            yield error
        if reset:
            current_attendances = [attendance]
