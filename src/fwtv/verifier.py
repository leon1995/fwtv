"""Contains logic for attendance verification."""

import dataclasses
import datetime

HOURS_6 = datetime.timedelta(hours=6)
HOURS_9 = datetime.timedelta(hours=9)
HOURS_10 = datetime.timedelta(hours=10)
MINUTES_30 = datetime.timedelta(minutes=30)
MINUTES_45 = datetime.timedelta(minutes=45)


@dataclasses.dataclass(frozen=True)
class Attendance:
    """A timespan relevant for verification."""

    clock_in: datetime.datetime
    clock_out: datetime.datetime

    def __post_init__(self):  # noqa: D105
        if self.clock_out <= self.clock_in:
            msg = f'Clocked out earlier or at the same time as clocked in for attendance {self}'
            raise ValueError(msg)

    def __str__(self) -> str:
        """Format this class as string."""
        return f'{type(self).__name__}(clock_in={self.clock_in!s}, clock_out={self.clock_out})'

    def __repr__(self) -> str:
        """Get the representation."""
        return str(self)


def calculate_time_attended(attendances: list[Attendance]) -> datetime.timedelta:
    """Calculate the time attended.

    :param attendances: list of attendances
    :return: time attended
    """
    attendances.sort(key=lambda x: x.clock_in)
    attended = datetime.timedelta()
    clock_out = None
    for attendance in attendances:
        # check overlaying attendances
        clock_in = attendance.clock_in if not clock_out or clock_out < attendance.clock_in else clock_out
        if not clock_out or clock_out < attendance.clock_out:
            clock_out = attendance.clock_out
            attended += clock_out - clock_in
    return attended


def calculate_break_time(attendances: list[Attendance]) -> datetime.timedelta:
    """Calculate the time between the specified attendances.

    :param attendances: list of attendances
    :return: time between attendances
    """
    if not attendances:
        return datetime.timedelta(seconds=0)
    attendances.sort(key=lambda x: x.clock_in)
    clock_in = attendances[0].clock_in
    attendances.sort(key=lambda x: x.clock_out)
    clock_out = attendances[-1].clock_out
    return clock_out - clock_in - calculate_time_attended(attendances)


@dataclasses.dataclass(frozen=True)
class Error:
    """Error found during verification."""

    reason: str
    attendances: list[Attendance]

    @property
    def days_affected(self) -> set[datetime.date]:
        """Get the days affected."""
        days: set[datetime.date] = set()
        for attendance in self.attendances:
            days = days.union({attendance.clock_in.date(), attendance.clock_out.date()})
        return days

    @property
    def break_time(self) -> datetime.timedelta:
        """Get the break time."""
        return calculate_break_time(self.attendances)

    @property
    def time_attended(self) -> datetime.timedelta:
        """Get the time attended."""
        return calculate_time_attended(self.attendances)


def verify_attendances(attendances: list[Attendance], tolerance: datetime.timedelta) -> list[Error]:
    """Verify that the specified attendances meet the requirements (in order).

    Requirements:
      1. It shall not be allowed to attend for more than 10 hours without not attended for at least 11 hours
      2. It shall not be allowed to attend for more than 9 hours without not attended for at least 45 minutes
      3. It shall not be allowed to attend for more than 6 hours without not attended for at least 30 minutes

    :param attendances: attendances to be verified
    :param tolerance: adjustable tolerance which is added to the limits
    :return: a list of errors found during verification
    """
    errors: list[Error] = []
    attendances.sort(key=lambda x: (x.clock_out, x.clock_out))  # ensure correct order
    # contains all attendances currently in verification
    # will be reset once a break of 11 hours has been reached
    current_attendances: list[Attendance] = []
    for attendance in attendances:
        current_attendances.sort(key=lambda x: x.clock_out)
        if current_attendances and attendance.clock_in > current_attendances[-1].clock_out:
            break_time = attendance.clock_in - current_attendances[-1].clock_out
        else:
            break_time = datetime.timedelta(seconds=0)  # first attendance, there is no break
        if break_time >= datetime.timedelta(hours=11):
            # reset relevant as 11-hour break has reached between previous attendances and current attendance
            current_attendances = [attendance]
        else:
            current_attendances.append(attendance)

        cumulated_time_attended = calculate_time_attended(current_attendances)
        cumulated_break_time = calculate_break_time(current_attendances)
        reason = None
        reset = False
        if cumulated_time_attended > HOURS_6 + tolerance and cumulated_break_time < MINUTES_30:
            reason = 'Attended more than 6 hours without a cumulated break of 30 min'
        if cumulated_time_attended > HOURS_9 + tolerance and cumulated_break_time < MINUTES_45:
            reason = 'Attended more than 9 hours without a cumulated break of 45 min'
        if cumulated_time_attended > HOURS_10 + tolerance:
            reason = 'Attended more than 10 hours without a single break of 11 hours'
            reset = True
        if reason:
            errors.append(Error(reason=reason, attendances=current_attendances[:]))
        if reset:
            # in order to avoid duplicate errors, reset the counter
            current_attendances = [attendance]
    return errors
