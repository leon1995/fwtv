import datetime
import json
import pathlib
import typing

import pytest

from fwtv import factorial

DATA_DIR = pathlib.Path(__file__).parent.joinpath('data')
EMPLOYEES = json.loads(DATA_DIR.joinpath('employees.json').read_text(encoding='utf-8'))
all_correct_attendances = json.loads(DATA_DIR.joinpath('all_correct.json').read_text(encoding='utf-8'))
hours_6 = json.loads(DATA_DIR.joinpath('6_hours_error.json').read_text(encoding='utf-8')) + all_correct_attendances
hours_9 = json.loads(DATA_DIR.joinpath('9_hours_error.json').read_text(encoding='utf-8')) + all_correct_attendances
hours_10 = json.loads(DATA_DIR.joinpath('10_hours_error.json').read_text(encoding='utf-8')) + all_correct_attendances
precondition_ = json.loads(DATA_DIR.joinpath('precondition.json').read_text(encoding='utf-8')) + all_correct_attendances


@pytest.mark.asyncio
@pytest.mark.parametrize("code, error", [(400, ValueError), (401, factorial.AuthenticationError)])
async def test_api_error(monkeypatch, code: int, error):
    class Response:
        def __init__(self, *_, **__):
            self.status = code

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_, **kwargs):
            pass

    async with factorial.FactorialApi(api_key='') as api:
        monkeypatch.setattr(api.session, 'get', Response)
        with pytest.raises(error):
            await api.get_employees()
        with pytest.raises(error):
            await api.get_attendances()


@pytest.mark.asyncio
async def test_response_json(monkeypatch):
    class Response:
        def __init__(self, *_, **__):
            self.status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_, **kwargs):
            pass

        @staticmethod
        async def json():
            return EMPLOYEES

    class EmployeeResponse(Response):

        @staticmethod
        async def json():
            return EMPLOYEES

    class AttendancesResponse(Response):

        @staticmethod
        async def json():
            return all_correct_attendances

    async with factorial.FactorialApi(api_key='') as api:
        monkeypatch.setattr(api.session, 'get', EmployeeResponse)
        assert await api.get_employees() == EMPLOYEES
        monkeypatch.setattr(api.session, 'get', AttendancesResponse)
        assert await api.get_attendances() == all_correct_attendances


@pytest.mark.parametrize("timestamp, expected", [("2023-01-01Z", datetime.datetime(2023, 1, 1)),
                                                 ("2023-02-02T11ZZ", datetime.datetime(2023, 2, 2, 11)),
                                                 ("2023-03-05T12:15ZZZ", datetime.datetime(2023, 3, 5, 12, 15))])
def test_convert_timestamp(timestamp: str, expected: datetime.datetime):
    actual = factorial.convert_timestamp(timestamp)
    assert actual == expected


scenario1 = (datetime.datetime(2023, 1, 5), datetime.datetime(2023, 3, 5), all_correct_attendances, EMPLOYEES, (0, 0))


@pytest.mark.parametrize("start, end, attendances, employees, error_count", [scenario1])
def test_error_detection_all_ok(start: datetime.datetime,
                                end: datetime.datetime,
                                attendances: factorial.LIST_JSON_RESPONSE,
                                employees: factorial.LIST_JSON_RESPONSE,
                                error_count: typing.Tuple[int, int]):
    preconditions, errors = factorial.get_errors(start, end, attendances, employees)
    assert len(preconditions) == error_count[0]
    assert len(errors) == error_count[1]


HOURS_6_SCENARIO = (datetime.datetime(2023, 1, 1),
                    datetime.datetime(2023, 3, 13),
                    hours_6,
                    EMPLOYEES,
                    1,
                    'Attended more than 6 hours without a cumulated break of 30 min')
HOURS_9_SCENARIO = (datetime.datetime(2023, 1, 1),
                    datetime.datetime(2023, 3, 13),
                    hours_9,
                    EMPLOYEES,
                    2,
                    'Attended more than 9 hours without a cumulated break of 45 min')
HOURS_10_SCENARIO = (datetime.datetime(2023, 1, 1),
                     datetime.datetime(2023, 3, 15),
                     hours_10,
                     EMPLOYEES,
                     2,
                     'Attended more than 10 hours without a single break of 11 hours')


@pytest.mark.parametrize("start, end, attendances, employees, error_count, reason",
                         [HOURS_6_SCENARIO, HOURS_9_SCENARIO, HOURS_10_SCENARIO])
def test_error_detection(start: datetime.datetime,
                         end: datetime.datetime,
                         attendances: factorial.LIST_JSON_RESPONSE,
                         employees: factorial.LIST_JSON_RESPONSE,
                         error_count: int,
                         reason: str):
    preconditions, errors = factorial.get_errors(start, end, attendances, employees)
    assert len(preconditions) == 0
    assert len(errors) == len(employees)
    for error in errors.values():
        assert len(error) == error_count
        for err in error:
            assert err.reason == reason


PRECONDITION_SCENARIO = (datetime.datetime(2023, 1, 1),
                         datetime.datetime(2023, 3, 15),
                         precondition_,
                         EMPLOYEES,
                         1)


@pytest.mark.parametrize("start, end, attendances, employees, error_count", [PRECONDITION_SCENARIO])
def test_precondition_detection(start: datetime.datetime,
                                end: datetime.datetime,
                                attendances: factorial.LIST_JSON_RESPONSE,
                                employees: factorial.LIST_JSON_RESPONSE,
                                error_count: int):
    preconditions, errors = factorial.get_errors(start, end, attendances, employees)
    assert len(preconditions) == len(employees)
    for precondition in preconditions.values():
        assert len(precondition) == error_count
    assert len(errors) == 0
