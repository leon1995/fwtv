"""State for managing data."""

import datetime
import logging
from collections.abc import Mapping

import anyio
import factorialhr
import reflex as rx

from factorialhr_analysis import constants, states


class DataState(rx.State):
    """State for managing data."""

    _employees: Mapping[int, factorialhr.Employee] = {}
    _teams: Mapping[int, factorialhr.Team] = {}
    _shifts: Mapping[int, factorialhr.AttendanceShift] = {}
    _credentials: factorialhr.Credentials | None = None
    _time_records: Mapping[int, factorialhr.TimeRecord] = {}
    _projects: Mapping[int, factorialhr.Project] = {}
    _project_workers: Mapping[int, factorialhr.ProjectWorker] = {}

    is_loading: rx.Field[bool] = rx.field(default=False)
    last_updated: rx.Field[datetime.datetime | None] = rx.field(default=None)

    @rx.var
    def len_of_shifts(self) -> int:
        """Get the number of shifts."""
        return len(self._shifts)

    async def _load_employees(self, api_client: factorialhr.ApiClient):
        employees = await factorialhr.EmployeesEndpoint(api_client).all()
        async with self:
            self._employees = {emp.id: emp for emp in employees.data()}

    async def _load_teams(self, api_client: factorialhr.ApiClient):
        teams = await factorialhr.TeamsEndpoint(api_client).all()
        async with self:
            self._teams = {team.id: team for team in teams.data()}

    async def _load_shifts(self, api_client: factorialhr.ApiClient):
        # all shifts are obtained in a single page and therefore requires a high timeout
        shifts = await factorialhr.ShiftsEndpoint(api_client).all(timeout=100)
        async with self:
            self._shifts = {shift.id: shift for shift in shifts.data()}

    async def _load_credentials(self, api_client: factorialhr.ApiClient):
        credentials = await factorialhr.CredentialsEndpoint(api_client).all()
        async with self:
            self._credentials = next(iter(credentials.data()), None)

    async def _load_time_records(self, api_client: factorialhr.ApiClient):
        # all time records are obtained in a single page and therefore requires a high timeout
        time_records = await factorialhr.TimeRecordEndpoint(api_client).all(timeout=100)
        async with self:
            self._time_records = {record.id: record for record in time_records.data()}

    async def _load_projects(self, api_client: factorialhr.ApiClient):
        projects = await factorialhr.ProjectEndpoint(api_client).all()
        async with self:
            self._projects = {project.id: project for project in projects.data()}

    async def _load_project_workers(self, api_client: factorialhr.ApiClient):
        project_workers = await factorialhr.ProjectWorkerEndpoint(api_client).all()
        async with self:
            self._project_workers = {project_worker.id: project_worker for project_worker in project_workers.data()}

    @rx.event
    async def refresh_data(self):  # noqa: ANN201
        """Refresh the data."""
        self.clear()
        if constants.API_KEY:
            return DataState.poll_data
        auth_state = await self.get_state(states.OAuthSessionState)
        if await auth_state.refresh_session():
            return DataState.poll_data
        return states.OAuthSessionState.redir

    @rx.event(background=True)
    async def poll_data(self):
        """Poll the data."""
        async with self:
            if self.is_loading:
                return
            self.is_loading = True
            auth = (await self.get_state(states.OAuthSessionState)).get_auth()
        try:
            async with (
                factorialhr.ApiClient(constants.ENVIRONMENT_URL, auth=auth) as client,
                anyio.create_task_group() as tg,
            ):
                tg.start_soon(self._load_teams, client)
                tg.start_soon(self._load_employees, client)
                tg.start_soon(self._load_shifts, client)
                tg.start_soon(self._load_credentials, client)
                tg.start_soon(self._load_time_records, client)
                tg.start_soon(self._load_projects, client)
                tg.start_soon(self._load_project_workers, client)
        except Exception:
            logging.getLogger(__name__).exception('error loading data')
            raise
        finally:
            async with self:
                self.is_loading = False
        async with self:
            self.last_updated = datetime.datetime.now(tz=datetime.UTC)
            logging.getLogger(__name__).info('data loaded')

    @rx.event
    def clear(self):
        """Clear the data."""
        self.last_updated = None
        self._employees.clear()
        self._teams.clear()
        self._shifts.clear()
        self._credentials = None
        self._time_records.clear()
        self._projects.clear()
        self._project_workers.clear()
