import datetime
import typing

import pytest

from fwtv import verifier


@pytest.mark.parametrize("clock_in, clock_out", [(datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
                                                  datetime.datetime(2023, 1, 1, 0, 0, 0, 0)),
                                                 (datetime.datetime(2023, 1, 1, 0, 0, 0, 1),
                                                  datetime.datetime(2023, 1, 1, 0, 0, 0, 0))])
def test_clock_in_earlier_than_clock_out(clock_in: datetime.datetime, clock_out: datetime.datetime):
    with pytest.raises(ValueError):
        verifier.Attendance(clock_in, clock_out)


@pytest.mark.parametrize("clock_in, clock_out", [(datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
                                                  datetime.datetime(2023, 1, 1, 0, 0, 0, 1))])
def test_str_and_repr(clock_in: datetime.datetime, clock_out: datetime.datetime):
    expected = f'Attendance(clock_in={str(clock_in)}, clock_out={str(clock_out)})'
    str_ = str(verifier.Attendance(clock_in, clock_out))
    assert str_ == expected
    repr_ = repr(verifier.Attendance(clock_in, clock_out))
    assert repr_ == expected


single_attendance = [verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 8),
                                         clock_out=datetime.datetime(2023, 1, 1, 10))]
normal_attendances = [verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 8),
                                          clock_out=datetime.datetime(2023, 1, 1, 10)),
                      verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 11),
                                          clock_out=datetime.datetime(2023, 1, 1, 14)),
                      verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 15),
                                          clock_out=datetime.datetime(2023, 1, 1, 20))]
attendances_with_intersection = [verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 8),
                                                     clock_out=datetime.datetime(2023, 1, 1, 10)),
                                 verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 9),
                                                     clock_out=datetime.datetime(2023, 1, 1, 14)),
                                 verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 13),
                                                     clock_out=datetime.datetime(2023, 1, 1, 20))]
begin_interception = [verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 8),
                                          clock_out=datetime.datetime(2023, 1, 1, 10)),
                      verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 9),
                                          clock_out=datetime.datetime(2023, 1, 1, 10)),
                      verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 13),
                                          clock_out=datetime.datetime(2023, 1, 1, 17)),
                      verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 13),
                                          clock_out=datetime.datetime(2023, 1, 1, 20)),
                      verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 14),
                                          clock_out=datetime.datetime(2023, 1, 1, 15)),
                      verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 15),
                                          clock_out=datetime.datetime(2023, 1, 1, 16))]
attendances_with_inception = [verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 8),
                                                  clock_out=datetime.datetime(2023, 1, 1, 10)),
                              verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 9),
                                                  clock_out=datetime.datetime(2023, 1, 1, 10)),
                              verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 13),
                                                  clock_out=datetime.datetime(2023, 1, 1, 17)),
                              verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 13),
                                                  clock_out=datetime.datetime(2023, 1, 1, 20)),
                              verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 14),
                                                  clock_out=datetime.datetime(2023, 1, 1, 15)),
                              verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 15),
                                                  clock_out=datetime.datetime(2023, 1, 1, 16)),
                              verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 15),
                                                  clock_out=datetime.datetime(2023, 1, 1, 21)),
                              verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 20),
                                                  clock_out=datetime.datetime(2023, 1, 1, 22))]
multiple_days = [verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 8),
                                     clock_out=datetime.datetime(2023, 1, 2, 2)),
                 verifier.Attendance(clock_in=datetime.datetime(2023, 1, 2, 18),
                                     clock_out=datetime.datetime(2023, 1, 3, 19)),
                 verifier.Attendance(clock_in=datetime.datetime(2023, 1, 3, 13),
                                     clock_out=datetime.datetime(2023, 1, 4, 5))]
random_order = [verifier.Attendance(clock_in=datetime.datetime(2023, 1, 15, 8),
                                    clock_out=datetime.datetime(2023, 1, 15, 10)),
                verifier.Attendance(clock_in=datetime.datetime(2023, 1, 14, 9),
                                    clock_out=datetime.datetime(2023, 1, 14, 10)),
                verifier.Attendance(clock_in=datetime.datetime(2023, 1, 20, 13),
                                    clock_out=datetime.datetime(2023, 1, 20, 17)),
                verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 13),
                                    clock_out=datetime.datetime(2023, 1, 1, 20)),
                verifier.Attendance(clock_in=datetime.datetime(2022, 12, 31, 14),
                                    clock_out=datetime.datetime(2022, 12, 31, 15)),
                verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 15),
                                    clock_out=datetime.datetime(2023, 1, 1, 16)),
                verifier.Attendance(clock_in=datetime.datetime(2023, 2, 4, 15),
                                    clock_out=datetime.datetime(2023, 2, 4, 21)),
                verifier.Attendance(clock_in=datetime.datetime(2023, 1, 1, 20),
                                    clock_out=datetime.datetime(2023, 1, 1, 22))]


@pytest.mark.parametrize("attendances, expected", [([], datetime.timedelta()),
                                                   (single_attendance, datetime.timedelta(hours=2)),
                                                   (normal_attendances, datetime.timedelta(hours=10)),
                                                   (attendances_with_intersection, datetime.timedelta(hours=12)),
                                                   (attendances_with_inception, datetime.timedelta(hours=11)),
                                                   (multiple_days, datetime.timedelta(hours=53)),
                                                   (random_order, datetime.timedelta(hours=23))])
def test_calculate_attended_time(attendances: typing.List[verifier.Attendance], expected: datetime.timedelta):
    actual = verifier.calculate_time_attended(attendances)
    assert actual == expected


@pytest.mark.parametrize("attendances, expected", [([], datetime.timedelta()),
                                                   (single_attendance, datetime.timedelta(hours=0)),
                                                   (normal_attendances, datetime.timedelta(hours=2)),
                                                   (begin_interception, datetime.timedelta(hours=3)),
                                                   (attendances_with_intersection, datetime.timedelta(hours=0)),
                                                   (attendances_with_inception, datetime.timedelta(hours=3)),
                                                   (multiple_days, datetime.timedelta(hours=16)),
                                                   (random_order, datetime.timedelta(hours=824))])
def test_calculate_break_time(attendances: typing.List[verifier.Attendance], expected: datetime.timedelta):
    actual = verifier.calculate_break_time(attendances)
    assert actual == expected


@pytest.mark.parametrize("attendances, expected", [(single_attendance, {datetime.date(2023, 1, 1)}),
                                                   (normal_attendances, {datetime.date(2023, 1, 1)}),
                                                   (attendances_with_intersection, {datetime.date(2023, 1, 1)}),
                                                   (attendances_with_inception, {datetime.date(2023, 1, 1)}),
                                                   (multiple_days, {datetime.date(2023, 1, 1),
                                                                    datetime.date(2023, 1, 2),
                                                                    datetime.date(2023, 1, 3),
                                                                    datetime.date(2023, 1, 4)}),
                                                   (random_order, {datetime.date(2023, 1, 1),
                                                                   datetime.date(2022, 12, 31),
                                                                   datetime.date(2023, 1, 15),
                                                                   datetime.date(2023, 1, 14),
                                                                   datetime.date(2023, 1, 20),
                                                                   datetime.date(2023, 2, 4)})])
def test_error_affected_days(attendances: typing.List[verifier.Attendance], expected: datetime.date):
    error = verifier.Error(reason='Test reason', attendances=attendances)
    assert error.days_affected == expected


@pytest.mark.parametrize("attendances, expected", [([], datetime.timedelta()),
                                                   (single_attendance, datetime.timedelta(hours=2)),
                                                   (normal_attendances, datetime.timedelta(hours=10)),
                                                   (attendances_with_intersection, datetime.timedelta(hours=12)),
                                                   (attendances_with_inception, datetime.timedelta(hours=11)),
                                                   (multiple_days, datetime.timedelta(hours=53)),
                                                   (random_order, datetime.timedelta(hours=23))])
def test_error_attended_time(attendances: typing.List[verifier.Attendance], expected: datetime.timedelta):
    error = verifier.Error(reason='Test reason', attendances=attendances)
    assert error.time_attended == expected


@pytest.mark.parametrize("attendances, expected", [([], datetime.timedelta()),
                                                   (single_attendance, datetime.timedelta(hours=0)),
                                                   (normal_attendances, datetime.timedelta(hours=2)),
                                                   (begin_interception, datetime.timedelta(hours=3)),
                                                   (attendances_with_intersection, datetime.timedelta(hours=0)),
                                                   (attendances_with_inception, datetime.timedelta(hours=3)),
                                                   (multiple_days, datetime.timedelta(hours=16)),
                                                   (random_order, datetime.timedelta(hours=824))])
def test_error_break_time(attendances: typing.List[verifier.Attendance], expected: datetime.timedelta):
    error = verifier.Error(reason='Test reason', attendances=attendances)
    assert error.break_time == expected


@pytest.mark.parametrize("attendances, error_count", [(single_attendance, 0),
                                                      (normal_attendances, 0),
                                                      (attendances_with_intersection, 1),
                                                      (attendances_with_inception, 1),
                                                      (multiple_days, 3),
                                                      (random_order, 2)])
def test_verify_work_time(attendances: typing.List[verifier.Attendance], error_count: int):
    errors = verifier.verify_attendances(attendances)
    assert len(errors) == error_count
