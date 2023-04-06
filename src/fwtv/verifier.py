import dataclasses
import datetime
import typing

HOURS_6 = datetime.timedelta(hours=6)
HOURS_9 = datetime.timedelta(hours=9)
HOURS_10 = datetime.timedelta(hours=10)
MINUTES_30 = datetime.timedelta(minutes=30)
MINUTES_45 = datetime.timedelta(minutes=45)


@dataclasses.dataclass(frozen=True)
class Attendance:
    """
    A timespan relevant for verification.
    """

    clock_in: datetime.datetime
    clock_out: datetime.datetime

    def __post_init__(self):
        if self.clock_out <= self.clock_in:
            raise ValueError(f"Clocked out earlier or at the same time as clocked in for attendance {self}")

    def __str__(self) -> str:
        return f"{type(self).__name__}(clock_in={str(self.clock_in)}, clock_out={self.clock_out})"

    def __repr__(self) -> str:
        return str(self)


def calculate_time_attended(attendances: typing.List[Attendance]) -> datetime.timedelta:
    """
    Calculates the time attended.

    @param attendances: list of attendances
    @return: time attended
    """
    attendances.sort(key=lambda x: x.clock_in)
    attended = datetime.timedelta()
    clock_out = None
    for i, attendance in enumerate(attendances):
        # check overlaying attendances
        if not clock_out or clock_out < attendance.clock_in:
            clock_in = attendance.clock_in
        else:
            clock_in = clock_out
        if not clock_out or clock_out < attendance.clock_out:
            clock_out = attendance.clock_out
            attended += clock_out - clock_in
    return attended


def calculate_break_time(attendances: typing.List[Attendance]) -> datetime.timedelta:
    """
    Calculates the time between the specified attendances.

    @param attendances: list of attendances
    @return: time between attendances
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
    """
    Error found during verification.
    """

    reason: str
    attendances: typing.List[Attendance]

    @property
    def days_affected(self) -> typing.Set[datetime.date]:
        days: typing.Set[datetime.date] = set()
        for attendance in self.attendances:
            days = days.union({attendance.clock_in.date(), attendance.clock_out.date()})
        return days

    @property
    def break_time(self) -> datetime.timedelta:
        return calculate_break_time(self.attendances)

    @property
    def time_attended(self) -> datetime.timedelta:
        return calculate_time_attended(self.attendances)


def verify_attendances(attendances: typing.List[Attendance]) -> typing.List[Error]:
    """
    Verifies that the specified attendances meet the following requirements (in order):
      1. It shall not be allowed to attend for more than 10 hours without not attended for at least 11 hours
      2. It shall not be allowed to attend for more than 9 hours without not attended for at least 45 minutes
      3. It shall not be allowed to attend for more than 6 hours without not attended for at least 30 minutes

    @param attendances: attendances to be verified
    @return: a list of errors found during verification
    """
    errors: typing.List[Error] = []
    attendances.sort(key=lambda x: (x.clock_out, x.clock_out))  # ensure correct order
    # contains all attendances currently in verification
    # will be reset once a break of 11 hours has been reached
    current_attendances: typing.List[Attendance] = []
    for i, attendance in enumerate(attendances):
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
        if cumulated_time_attended > HOURS_6 and cumulated_break_time < MINUTES_30:
            reason = "Attended more than 6 hours without a cumulated break of 30 min"
        if cumulated_time_attended > HOURS_9 and cumulated_break_time < MINUTES_45:
            reason = "Attended more than 9 hours without a cumulated break of 45 min"
        if cumulated_time_attended > HOURS_10:
            reason = "Attended more than 10 hours without a single break of 11 hours"
            reset = True
        if reason:
            errors.append(Error(reason=reason, attendances=current_attendances[:]))
        if reset:
            # in order to avoid duplicate errors, reset the counter
            current_attendances = [attendance]
    return errors
