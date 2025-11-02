"""State for managing project calculations."""

import collections
import datetime
import logging

import anyio
import factorialhr
import reflex as rx

from factorialhr_analysis import states

DECEMBER = 12  # Month number for December


async def _anyio_gather(*coros: collections.abc.Coroutine) -> tuple:
    """Gather results from coroutines using anyio."""
    results: list = []

    async def collect(index: int, coro: collections.abc.Coroutine) -> None:
        result = await coro
        results.insert(index, result)

    async with anyio.create_task_group() as tg:
        for index, coro in enumerate(coros):
            tg.start_soon(collect, index, coro)

    return tuple(results)


class ProjectSettingsState(rx.State):
    """State for managing project settings."""

    _start_date: datetime.date | None = None
    _end_date: datetime.date | None = None
    active: rx.Field[bool] = rx.field(default=True)

    @rx.var
    def start_date(self) -> str:
        """Get the start date as a string."""
        if self._start_date is None:
            return ''
        return self._start_date.isoformat()

    @rx.var
    def end_date(self) -> str:
        """Get the end date as a string."""
        if self._end_date is None:
            return ''
        return self._end_date.isoformat()

    @rx.event
    def set_start_date(self, date: str):
        """Set the start date."""
        if date:
            self._start_date = datetime.date.fromisoformat(date)
        else:
            self._start_date = None

    @rx.event
    def set_end_date(self, date: str):
        """Set the end date."""
        if date:
            self._end_date = datetime.date.fromisoformat(date)
        else:
            self._end_date = None

    @rx.var
    def date_error(self) -> bool:
        """Check if the end date is before the start date."""
        if not self._start_date or not self._end_date:
            return False
        return self._end_date < self._start_date

    @rx.event
    def set_active(self, value: bool):  # noqa: FBT001
        """Set the active projects."""
        self.active = value


class ProjectState(rx.State):
    """State for managing project calculations."""

    is_loading_projects_times: rx.Field[bool] = rx.field(default=False)
    is_loading_unrelated_minutes: rx.Field[bool] = rx.field(default=False)
    calculation_type: rx.Field[str] = rx.field(default='imputed')  # 'imputed' or 'unrelated'

    @rx.event
    def set_calculation_type(self, value: str | list[str]):
        """Set the calculation type."""
        # Handle both str and list[str] from segmented_control
        self.calculation_type = value if isinstance(value, str) else (value[0] if value else 'imputed')

    # Imputed minutes data
    project_times_data: rx.Field[list[dict]] = rx.field(default_factory=list)
    employee_names: rx.Field[list[str]] = rx.field(default_factory=list)
    project_names: rx.Field[list[str]] = rx.field(default_factory=list)

    @rx.var
    def chart_height(self) -> int:
        """Calculate chart height based on number of projects."""
        num_projects = len(self.project_names)
        if num_projects == 0:
            return 400
        # Base height of 200px + 50px per project
        return 200 + (num_projects * 50)

    def _validate_calculation_inputs(
        self, settings_state: 'ProjectSettingsState', data_state: 'states.DataState'
    ) -> str | None:
        """Validate inputs for calculation. Returns error message if invalid, None otherwise."""
        if settings_state._start_date is None or settings_state._end_date is None:  # noqa: SLF001
            return 'Please select both start and end dates'
        if not data_state._time_records:  # noqa: SLF001
            return 'No project time records found'
        if not data_state._projects:  # noqa: SLF001
            return 'No projects found'
        return None

    def _process_time_records(
        self,
        data_state: 'states.DataState',
        settings_state: 'ProjectSettingsState',
    ) -> tuple[collections.defaultdict[str, collections.defaultdict[str, int]], set[str]]:
        """Process time records and calculate project times by employee."""
        project_times_by_employee_name: collections.defaultdict[str, collections.defaultdict[str, int]] = (
            collections.defaultdict(lambda: collections.defaultdict(int))
        )
        contributed_projects: set[str] = set()

        start_date = settings_state._start_date  # noqa: SLF001
        end_date = settings_state._end_date  # noqa: SLF001
        active_only = settings_state.active

        for record in data_state._time_records.values():  # noqa: SLF001
            if record.date is None or record.date < start_date or record.date > end_date:
                continue
            project_worker = data_state._project_workers.get(record.project_worker_id)  # noqa: SLF001
            if not project_worker:
                continue

            if (
                project_worker.project_id in data_state._projects  # noqa: SLF001
                and project_worker.employee_id in data_state._employees  # noqa: SLF001
            ):
                if record.imputed_minutes is None:
                    continue
                employee_name = data_state._employees[project_worker.employee_id].full_name  # noqa: SLF001
                project = data_state._projects[project_worker.project_id]  # noqa: SLF001
                if active_only and project.status != factorialhr.ProjectStatus.ACTIVE:
                    continue
                project_times_by_employee_name[employee_name][project.name] += record.imputed_minutes or 0
                contributed_projects.add(project.name)

        return project_times_by_employee_name, contributed_projects

    def _prepare_chart_data(
        self,
        project_times_by_employee_name: collections.defaultdict[str, collections.defaultdict[str, int]],
        contributed_projects: set[str],
    ) -> tuple[list[dict], list[str], list[str]]:
        """Prepare chart data from processed project times."""
        project_times_sum_by_project_name: collections.defaultdict[str, int] = collections.defaultdict(int)
        for project_times in project_times_by_employee_name.values():
            for project_name, minutes in project_times.items():
                project_times_sum_by_project_name[project_name] += minutes

        employee_names = sorted(project_times_by_employee_name.keys())
        project_names = sorted(contributed_projects)

        chart_data = []
        for project_name in project_names:
            row: dict = {
                'project': project_name,
                'total': project_times_sum_by_project_name[project_name],
            }
            for employee_name in employee_names:
                row[employee_name] = project_times_by_employee_name[employee_name].get(project_name, 0)
            chart_data.append(row)

        return chart_data, employee_names, project_names

    # Unrelated minutes data
    unrelated_minutes_data: rx.Field[list[dict]] = rx.field(default_factory=list)
    total_unrelated_minutes: rx.Field[int] = rx.field(default=0)

    error_message: rx.Field[str | None] = rx.field(default=None)

    @rx.event(background=True)
    async def calculate_imputed_minutes(self):
        """Calculate imputed minutes for projects."""
        async with self:
            if self.is_loading_projects_times:
                return
            self.is_loading_projects_times = True
            self.error_message = None
            self.project_times_data = []
            self.employee_names = []
            self.project_names = []

        async with self:
            settings_state = await self.get_state(ProjectSettingsState)
            data_state = await self.get_state(states.DataState)

        error_message = self._validate_calculation_inputs(settings_state, data_state)
        if error_message:
            async with self:
                self.error_message = error_message
                self.is_loading_projects_times = False
            return

        project_times_by_employee_name, contributed_projects = self._process_time_records(data_state, settings_state)

        chart_data, employee_names, project_names = self._prepare_chart_data(
            project_times_by_employee_name, contributed_projects
        )

        async with self:
            self.project_times_data = chart_data
            self.employee_names = employee_names
            self.project_names = project_names
            self.is_loading_projects_times = False
            self.error_message = None

    @rx.event(background=True)
    async def calculate_unrelated_minutes(self):
        """Calculate minutes not assigned to any project."""
        async with self:
            if self.is_loading_unrelated_minutes:
                return
            self.is_loading_unrelated_minutes = True
            self.error_message = None
            self.unrelated_minutes_data = []
            self.total_unrelated_minutes = 0

        async with self:
            settings_state = await self.get_state(ProjectSettingsState)
            data_state = await self.get_state(states.DataState)

        if settings_state._start_date is None or settings_state._end_date is None:  # noqa: SLF001
            async with self:
                self.error_message = 'Please select both start and end dates'
                self.is_loading_unrelated_minutes = False
            return

        try:
            # Use data from DataState instead of making API calls
            start_date = settings_state._start_date  # noqa: SLF001
            end_date = settings_state._end_date  # noqa: SLF001

            # Filter shifts by date range
            filtered_shifts = [
                shift
                for shift in data_state._shifts.values()  # noqa: SLF001
                if start_date <= shift.date <= end_date
            ]

            # Filter time records by date range and get their shift IDs
            filtered_time_records = [
                record
                for record in data_state._time_records.values()  # noqa: SLF001
                if record.date is not None and start_date <= record.date <= end_date
            ]

            if not filtered_shifts:
                async with self:
                    self.error_message = 'No shifts found in selected date range'
                    self.is_loading_unrelated_minutes = False
                return

            if not filtered_time_records:
                async with self:
                    self.error_message = 'No project time records found in selected date range'
                    self.is_loading_unrelated_minutes = False
                return

            # Map time records by shift ID
            records_by_shift_id = {record.attendance_shift_id: record for record in filtered_time_records}

            # Find unrelated shifts
            unrelated_shifts_by_employee_id: collections.defaultdict[int, list[factorialhr.AttendanceShift]] = (
                collections.defaultdict(list)
            )

            for shift in filtered_shifts:
                if (
                    shift.id is not None
                    and shift.id not in records_by_shift_id
                    and shift.employee_id is not None
                    and shift.employee_id in data_state._employees  # noqa: SLF001
                ):
                    unrelated_shifts_by_employee_id[shift.employee_id].append(shift)

            # Calculate totals
            chart_data = []
            total_minutes = 0
            for eid, shifts_list in unrelated_shifts_by_employee_id.items():
                employee = data_state._employees[eid]  # noqa: SLF001
                if settings_state.active and not employee.active:
                    continue
                minutes = sum(shift.minutes for shift in shifts_list)
                total_minutes += minutes
                chart_data.append({'employee': employee.full_name, 'minutes': minutes})

            # Sort by minutes descending
            chart_data.sort(key=lambda x: x['minutes'], reverse=True)

            async with self:
                self.unrelated_minutes_data = chart_data
                self.total_unrelated_minutes = total_minutes
                self.is_loading_unrelated_minutes = False
                self.error_message = None

        except Exception as e:
            logging.getLogger(__name__).exception('error calculating unrelated minutes')
            async with self:
                self.error_message = str(e)
                self.is_loading_unrelated_minutes = False

    @rx.event
    async def calculate(self):
        """Calculate both imputed and unrelated minutes."""
        yield ProjectState.calculate_imputed_minutes
        yield ProjectState.calculate_unrelated_minutes
