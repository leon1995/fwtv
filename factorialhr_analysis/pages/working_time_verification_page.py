"""The main page of the app."""

import asyncio
import collections
import csv
import datetime
import io
import os
import typing
from collections.abc import Container, Sequence

import anyio.from_thread
import factorialhr
import reflex as rx
from reflex.utils.prerequisites import get_app

from factorialhr_analysis import templates, working_time_verification, components, states


def time_to_moment(time_: datetime.time | None) -> rx.MomentDelta:
    """Convert a datetime.time to a rx.MomentDelta."""
    if time_ is None:
        return rx.MomentDelta()
    return rx.MomentDelta(hours=time_.hour, minutes=time_.minute, seconds=time_.second)


class Attendance(typing.TypedDict):
    """TypedDict for attendance."""

    date: datetime.date
    clock_in: rx.MomentDelta
    clock_out: rx.MomentDelta
    minutes: rx.MomentDelta


class ErrorToShow(typing.TypedDict):
    """TypedDict for errors to show."""

    name: str
    affected_days: str
    error: str
    cumulated_break: datetime.timedelta
    cumulated_attendance: datetime.timedelta

    attendances: Sequence[Attendance]


class DataState(rx.State):
    """State holding all the data."""

    _shifts: collections.defaultdict[int, list[factorialhr.AttendanceShift]] = collections.defaultdict(  # noqa: RUF012
        list
    )  # employee id as key
    _employees: list[factorialhr.Employee] = []  # noqa: RUF012
    _employee_team_name_mapping: dict[int, list[str]] = {}  # noqa: RUF012
    calculated_errors: list[working_time_verification.Error] = []  # noqa: RUF012
    errors_to_show: list[ErrorToShow] = []  # noqa: RUF012
    start_date: str = ''
    end_date: str = ''
    is_loading: bool = False  # Guard flag
    tolerance: str = ''
    processed_employees: int = 0  # Number of employees processed so far

    filter_value: str = ''  # Placeholder for search functionality

    selected_error_ids: list[int] = []  # noqa: RUF012

    @rx.var
    def date_error(self) -> bool:
        """Check if the end date is before the start date."""
        if not self.start_date or not self.end_date:
            return False
        return datetime.date.fromisoformat(self.end_date) < datetime.date.fromisoformat(self.start_date)

    @rx.var
    def disable_submit(self) -> bool:
        """Disable the submit button if there is a date error."""
        return self.date_error or not self.start_date or not self.end_date

    def _should_cancel(self) -> bool:
        """Check if the current session is still valid."""
        return self.router.session.client_token not in get_app().app.event_namespace.token_to_sid

    def _cleanup(self):
        """Cleanup method to reset state."""
        self._shifts = collections.defaultdict(list)
        self.processed_employees = 0
        self.errors_to_show = []
        self._employees = []
        self._employee_team_name_mapping = {}
        self.selected_error_ids = []
        self.is_loading = False

    @rx.var
    def length_of_employees(self) -> int:
        """Get the length of employees."""
        return len(self._employees)

    async def _handle_employee(
        self, client: factorialhr.ApiClient, employee: factorialhr.Employee, teams: Sequence[factorialhr.Team]
    ):
        """Handle fetching shifts for an employee."""
        async with self:
            self._employees.append(employee)
            self._employee_team_name_mapping[employee.id] = [
                t.name for t in teams if t.employee_ids and employee.id in t.employee_ids
            ]
        shifts = await factorialhr.ShiftsEndpoint(client).all(
            params={'start_on': self.start_date, 'end_on': self.end_date, 'employee_ids[]': [employee.id]},
            timeout=60,
        )
        async with self:
            for shift in shifts.data():
                if self._should_cancel():
                    self._cleanup()
                    return
                self._shifts[employee.id].append(shift)

    @rx.event(background=True)
    async def handle_submit(self, form_data: dict):
        """Fetch employees and teams data."""
        async with self:
            if self.is_loading:
                return

            self.start_date = form_data.get('start_date')
            self.end_date = form_data.get('end_date')
            self.is_loading = True
            self._shifts = collections.defaultdict(list)
            self.processed_employees = 0
            self.errors_to_show = []
            self._employees = []
            self._employee_team_name_mapping = {}
            self.selected_error_ids = []
        yield  # Send initial state update to frontend

        try:
            async with self:
                api_session = (await self.get_state(states.OAuthSessionState)).get_auth()
            # API calls outside async with block
            async with factorialhr.ApiClient(os.environ['FACTORIALHR_ENVIRONMENT_URL'], auth=api_session) as client:
                employees = await factorialhr.EmployeesEndpoint(client).all()
                teams = list((await factorialhr.TeamsEndpoint(client).all()).data())
                async with anyio.from_thread.create_task_group() as tg:
                    for employee in employees.data():
                        tg.start_soon(self._handle_employee, client, employee, teams)

            async with self:
                yield DataState.fill_errors_to_show  # set is_loading to false

        except asyncio.CancelledError:
            # Handle cancellation when page is reloaded/closed
            async with self:
                self._cleanup()
            raise
        except Exception:
            # Handle other errors
            async with self:
                self._cleanup()
            raise

    @rx.event
    async def fill_errors_to_show(self):
        """Fill the errors_to_show list based on the fetched data."""
        self.selected_error_ids = []
        self.errors_to_show = []
        self.processed_employees = 0
        self.is_loading = True
        yield
        tolerance = datetime.timedelta(minutes=int(self.tolerance) if self.tolerance.isdigit() else 0)
        value = self.filter_value.lower()
        for employee in self._employees:
            teams = self._employee_team_name_mapping.get(employee.id, [])
            if value in employee.full_name.lower() or any(value in team.lower() for team in teams):
                for error in working_time_verification.get_error(self._shifts[employee.id], tolerance=tolerance):
                    if self._should_cancel():
                        self._cleanup()
                        return
                    self.errors_to_show.append(
                        ErrorToShow(
                            name=employee.full_name,
                            affected_days=', '.join(str(d) for d in error.days_affected),
                            error=error.reason,
                            cumulated_break=error.break_time,
                            cumulated_attendance=error.time_attended,
                            attendances=[
                                Attendance(
                                    date=a.date,
                                    clock_in=time_to_moment(a.clock_in) if a.clock_in is not None else None,
                                    clock_out=time_to_moment(a.clock_out) if a.clock_out is not None else None,
                                    minutes=rx.MomentDelta(minutes=a.minutes),
                                )
                                for a in error.attendances
                            ],
                        )
                    )
                    yield
            self.processed_employees += 1
        self.is_loading = False

    @rx.event
    def filter_employees(self, value: str):
        """Filter employees based on the search value."""
        self.filter_value = value
        yield DataState.fill_errors_to_show

    @rx.event
    def set_tolerance(self, value: str):
        """Set the tolerance value."""
        if value == '' or value.isdigit():
            self.tolerance = value
        yield DataState.fill_errors_to_show

    @rx.event
    def select_row(self, index: int):
        """Handle row selection."""
        if index in self.selected_error_ids:
            self.selected_error_ids.remove(index)
        else:
            self.selected_error_ids.append(index)

    def _convert_to_csv(self, indices: Container[int]) -> str:
        # Create a string buffer to hold the CSV data
        with io.StringIO() as output:
            writer = csv.DictWriter(
                output, fieldnames=['Name', 'Affected Days', 'Cumulated Break', 'Cumulated Attendance', 'Error']
            )
            writer.writeheader()
            for index, error in enumerate(self.errors_to_show):
                if index in indices:
                    writer.writerow(
                        {
                            'Name': error['name'],
                            'Affected Days': error['affected_days'],
                            'Cumulated Break': error['cumulated_break'],
                            'Cumulated Attendance': error['cumulated_attendance'],
                            'Error': error['error'],
                        }
                    )

            # Get the CSV data as a string
            return output.getvalue()

    @rx.event
    def download(self, data: str):
        """Download the given data as a CSV file."""
        file_name = (
            f'{self.start_date}-{self.end_date}_errors.csv' if self.start_date and self.end_date else 'errors.csv'
        )
        yield rx.download(
            data=data,
            filename=file_name,
        )

    @rx.event
    def download_all_errors(self):
        """Download all errors as a CSV file."""
        csv_data = self._convert_to_csv(range(len(self.errors_to_show)))
        yield self.download(csv_data)

    @rx.event
    def download_selected_errors(self):
        """Download selected errors as a CSV file."""
        csv_data = self._convert_to_csv(self.selected_error_ids)
        yield self.download(csv_data)


def render_input() -> rx.Component:
    """Render the date input form."""
    return rx.form(
        rx.hstack(
            rx.text('Start date'),
            rx.input(
                type='date',
                name='start_date',
                value=DataState.start_date,
                on_change=DataState.set_start_date,
            ),
            rx.text('End date'),
            rx.input(
                type='date',
                name='end_date',
                value=DataState.end_date,
                on_change=DataState.set_end_date,
            ),
            rx.button(
                'Submit',
                type='submit',
                loading=DataState.is_loading,
                disabled=DataState.disable_submit,
            ),
            rx.cond(
                DataState.date_error,
                rx.text('End date must be after start date', color='red'),
            ),
            spacing='3',
            align='center',
            width='100%',
        ),
        on_submit=DataState.handle_submit,
        width='100%',
    )


def render_export_buttons() -> rx.Component:
    """Render the export buttons."""
    return rx.hstack(
        rx.button(
            'Export Selected',
            disabled=DataState.selected_error_ids.length() == 0,
            on_click=DataState.download_selected_errors,
        ),
        rx.button(
            'Export All', disabled=DataState.errors_to_show.length() == 0, on_click=DataState.download_all_errors
        ),
        justify='center',
        align='center',
        width='100%',
    )


def render_search() -> rx.Component:
    """Render the search input."""
    return rx.hstack(
        rx.text('Search'),
        rx.input(
            value=DataState.filter_value,
            on_change=DataState.filter_employees,
            width='100%',
            placeholder='Filter by name or team',
        ),
        width='50%',
        align='center',
    )


def render_tolerance_input() -> rx.Component:
    """Render the tolerance input."""
    return rx.hstack(
        rx.text('Tolerance'),
        rx.input(
            placeholder='Minutes',
            type='number',
            value=DataState.tolerance,
            on_change=DataState.set_tolerance,
            width='100%',
            regex=r'^\d*$',
            min=0,
        ),
        width='25%',
        align='center',
    )


def render_filters() -> rx.Component:
    """Render the filters section."""
    return rx.hstack(
        render_tolerance_input(),
        render_search(),
        width='100%',
        align='center',
        justify='end',
    )


def show_employee(error: rx.Var[ErrorToShow], index: int) -> rx.Component:
    """Show a customer in a table row."""
    return rx.table.row(
        rx.table.cell(error['name']),
        rx.table.cell(error['affected_days']),
        rx.table.cell(error['cumulated_break']),
        rx.table.cell(error['cumulated_attendance']),
        rx.table.cell(error['error'], align='left'),
        rx.table.cell(
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.icon_button('info'),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title('Relevant attendance records'),
                    rx.inset(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell('Date'),
                                    rx.table.column_header_cell('Clock in'),
                                    rx.table.column_header_cell('Clock out'),
                                    rx.table.column_header_cell('Hours attended'),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    error['attendances'],
                                    lambda x: rx.table.row(
                                        rx.table.cell(rx.moment(x['date'], format='YYYY-MM-DD')),
                                        rx.table.cell(
                                            rx.cond(
                                                x['clock_in'].is_none(),
                                                None,
                                                rx.moment(x['date'], add=x['clock_in'], format='HH:mm'),
                                            )
                                        ),
                                        rx.table.cell(
                                            rx.cond(
                                                x['clock_out'].is_none(),
                                                None,
                                                rx.moment(x['date'], add=x['clock_out'], format='HH:mm'),
                                            )
                                        ),
                                        rx.table.cell(rx.moment(x['date'], add=x['minutes'], format='HH:mm')),
                                    ),
                                )
                            ),
                        ),
                        side='x',
                        margin_top='24px',
                        margin_bottom='24px',
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button(
                                'Close',
                                variant='soft',
                            ),
                        ),
                        justify='end',
                    ),
                ),
            ),
            align='right',
        ),
        on_click=lambda: DataState.select_row(index),
        background_color=rx.cond(DataState.selected_error_ids.contains(index), rx.color('blue', 3), 'transparent'),
    )


def render_table() -> rx.Component:
    """Render the main table showing errors."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell('Name', min_width='17.5%', max_width='17.5%'),
                rx.table.column_header_cell('Affected Days', min_width='15%', max_width='15%'),
                rx.table.column_header_cell('Cumulated Break', min_width='12.5%', max_width='12.5%'),
                rx.table.column_header_cell('Cumulated Attendance', min_width='12.5%', max_width='12.5%'),
                rx.table.column_header_cell('Error', min_width='40%', max_width='40%'),
                rx.table.column_header_cell('Records', align='right', min_width='2.5%', max_width='2.5%'),
            ),
        ),
        rx.table.body(
            rx.foreach(
                DataState.errors_to_show,
                show_employee,
            )
        ),
        width='100%',
    )


def live_progress() -> rx.Component:
    """Show a live progress bar when loading data."""
    return rx.cond(
        ~DataState.is_loading,
        rx.fragment(),
        rx.progress(value=DataState.processed_employees, max=DataState.length_of_employees),
    )


@components.requires_authentication
@templates.template
def working_time_verification_page() -> rx.Component:
    """Index page of the app."""
    return rx.vstack(
        rx.hstack(render_input(), render_export_buttons(), render_filters(), justify='between', width='100%'),
        live_progress(),
        render_table(),
        width='100%',
    )
