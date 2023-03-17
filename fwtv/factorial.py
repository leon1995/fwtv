import collections
import datetime
import typing

import aiohttp
from tabulate import tabulate

from fwtv import verifier

LIST_JSON_RESPONSE = typing.List[typing.Dict[str, typing.Any]]
GET_ERRORS = typing.Tuple[typing.Dict[str, typing.List[str]], typing.Dict[str, typing.List[verifier.Error]]]


class AuthenticationError(Exception):
    """
    Exception to be raised if there was an error authenticating.
    """


class FactorialApi:
    """
    Factorial api wrapper providing methods to get all employees and attendances.
    """

    def __init__(self, api_key: str, base_url="https://api.factorialhr.com"):
        self.headers = {"accept": "application/json", "x-api-key": api_key}
        self.session = aiohttp.ClientSession(base_url, headers=self.headers)

    async def close(self):
        await self.session.close()

    async def __aexit__(self, *_, **__):
        await self.close()

    async def __aenter__(self) -> "FactorialApi":
        return self

    async def _get(self, endpoint: str) -> typing.Any:
        async with self.session.get("/api/" + endpoint) as resp:
            if resp.status == 401:
                raise AuthenticationError("Authentication failed because the api key may be invalid")
            elif resp.status != 200:
                raise ValueError(f'Error getting "/api/{endpoint}": {resp.status}')
            return await resp.json()

    async def get_attendances(self) -> LIST_JSON_RESPONSE:
        return typing.cast(LIST_JSON_RESPONSE, await self._get("v2/time/attendance"))

    async def get_employees(self) -> LIST_JSON_RESPONSE:
        return typing.cast(LIST_JSON_RESPONSE, await self._get("v2/core/employees"))


def convert_timestamp(timestamp: str) -> datetime.datetime:
    """
    Converts iso timestamp to datetime

    @param timestamp: iso timestamp
    @return: converted timestamp
    """
    return datetime.datetime.fromisoformat(timestamp.replace("Z", ""))


def get_errors(
        start: datetime.datetime, end: datetime.datetime, attendances: LIST_JSON_RESPONSE, employees: LIST_JSON_RESPONSE
) -> GET_ERRORS:
    preconditions: typing.Dict[str, typing.List[str]] = collections.defaultdict(list)
    errors: typing.Dict[str, typing.List[verifier.Error]] = collections.defaultdict(list)
    for employee in employees:
        name = employee["full_name"]
        employee_attendances: typing.List[verifier.Attendance] = []

        for attendance in filter(lambda x: x["employee_id"] == employee["id"], attendances):
            if "clock_in" not in attendance or not attendance["clock_in"]:
                preconditions[name].append(f'no clock in time provided for attendance with id "{attendance["id"]}"')
                continue
            clock_in = convert_timestamp(attendance["clock_in"])
            if clock_in < start or clock_in > end:
                continue
            if "clock_out" not in attendance or not attendance["clock_out"]:
                preconditions[name].append(f'no clock out time provided for clock in time "{clock_in}"')
                continue
            if not attendance["workable"]:
                continue  # it has been declared as a break
            try:
                a = verifier.Attendance(clock_in=clock_in, clock_out=convert_timestamp(attendance["clock_out"]))
                employee_attendances.append(a)
            except ValueError as e:
                preconditions[name].append(str(e))
                continue
        errors_ = verifier.verify_attendances(employee_attendances)
        if errors_:
            errors[name] = errors_
    return preconditions, errors


def cli():  # pragma: no cover
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        "Fetch attendances and employees from FactorialHR api and verify that the " "work time comply with german rules"
    )
    parser.add_argument("start", type=datetime.datetime.fromisoformat, help="Start iso 8601 formatted timestamp")
    parser.add_argument("end", type=datetime.datetime.fromisoformat, help="End iso 8601 formatted timestamp")
    parser.add_argument("api_key", type=str, help="Company api key")
    args = parser.parse_args()

    async def fetch_data() -> typing.Tuple[LIST_JSON_RESPONSE, LIST_JSON_RESPONSE]:
        async with FactorialApi(args.api_key) as api:
            _attendances = await api.get_attendances()
            _employees = await api.get_employees()
        return _employees, _attendances

    employees, attendances = asyncio.run(fetch_data())

    preconditions, errors = get_errors(args.start, args.end, attendances, employees)
    entries = []
    for name, error in preconditions.items():
        for e in error:
            entries.append([name, e])
    print("Precondition errors")
    print(tabulate(entries, headers=["Name", "Error"], tablefmt="orgtbl"))
    print("")

    headers = ["Name", "Day(s)", "Reason", "Break", "Attended"]
    entries = []
    for name, error in errors.items():
        for i, e in enumerate(error):
            affected_days = [str(day) for day in e.days_affected]
            affected_days.sort()
            entries.append([name, ", ".join(affected_days), e.reason, str(e.break_time), str(e.time_attended)])
            if i + 1 == len(error):
                entries.append(["", "", "", "", ""])
    print("Working time verification failures")
    print(tabulate(entries[:-1], headers=headers, tablefmt="orgtbl"))
