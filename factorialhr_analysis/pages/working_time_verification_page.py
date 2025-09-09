"""The main page of the app."""

import csv
import datetime
import io
import typing
from collections.abc import Container, Iterable, Sequence

import anyio.from_thread
import factorialhr
import reflex as rx
from reflex.utils.prerequisites import get_app

from factorialhr_analysis import components, states, templates, working_time_verification


class SettingsState(rx.State):
    _start_date: datetime.date | None = None
    _end_date: datetime.date | None = None
    _tolerance: datetime.timedelta | None = None

    only_active: rx.Field[bool] = rx.field(default=True)

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

    @rx.var
    def tolerance(self) -> str:
        """Get the tolerance value."""
        return str(int(self._tolerance.total_seconds() / 60)) if self._tolerance is not None else ''

    @rx.event
    def set_tolerance(self, value: str):
        """Set the tolerance value."""
        if value.isdigit():
            self._tolerance = datetime.timedelta(minutes=int(value))
        else:
            self._tolerance = None

    @rx.event
    def set_start_date(self, date: str):
        """Set the start date."""
        self._start_date = datetime.date.fromisoformat(date)

    @rx.event
    def set_end_date(self, date: str):
        """Set the end date."""
        self._end_date = datetime.date.fromisoformat(date)

    @rx.var
    def date_error(self) -> bool:
        """Check if the end date is before the start date."""
        if not self._start_date or not self._end_date:
            return False
        return self._end_date < self._start_date

    @rx.event
    def set_only_active(self, active: bool):  # noqa: FBT001
        """Set whether to only include active employees."""
        self.only_active = active


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
    team_names: Iterable[str]
    affected_days: str
    error: str
    cumulated_break: datetime.timedelta
    cumulated_attendance: datetime.timedelta

    attendances: Sequence[Attendance]


def _filter_error(filter_value: str, error: ErrorToShow) -> bool:
    return filter_value in error['name'].lower() or any(
        filter_value in team_name.lower() for team_name in error['team_names']
    )


class DataStateDeprecated(rx.State):
    """State holding all the data."""

    errors_to_show: rx.Field[list[ErrorToShow]] = rx.field(default_factory=list)
    _calculated_errors: list[ErrorToShow] = []  # noqa: RUF012
    is_loading: rx.Field[bool] = rx.field(default=False)
    processed_employees: rx.Field[int] = rx.field(0)  # Number of employees processed so far
    total_amount_of_employees: rx.Field[int] = rx.field(0)

    filter_value: rx.Field[str] = rx.field('')  # Placeholder for search functionality

    selected_error_ids: rx.Field[list[int]] = rx.field(default_factory=list)

    def _should_cancel(self) -> bool:
        """Check if the current session is still valid."""
        return self.router.session.client_token not in get_app().app.event_namespace.token_to_sid

    async def _handle_single_employee(
        self,
        employee: factorialhr.Employee,
        teams: Sequence[factorialhr.Team],
        shifts: Sequence[factorialhr.AttendanceShift],
        tolerance: datetime.timedelta | None,
    ):
        """Handle a single employee."""
        for error in working_time_verification.get_error(
            filter(lambda x: x.employee_id == employee.id, shifts), tolerance=tolerance
        ):
            async with self:
                error_to_show = ErrorToShow(
                    name=employee.full_name,
                    team_names=[team.name for team in teams if employee.id in team.employee_ids],
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
                self._calculated_errors.append(error_to_show)
        async with self:
            self.processed_employees += 1

    @rx.event(background=True)
    async def calculate_errors(self):
        """Calculate errors based on the shifts."""
        async with self:
            if self.is_loading:
                return
            self.is_loading = True
            self.selected_error_ids.clear()
            self.errors_to_show.clear()
            self._calculated_errors.clear()
            self.processed_employees = 0
            data_state = await self.get_state(states.DataState)
            settings_state = await self.get_state(SettingsState)

        async with self:
            employees = [
                employee
                for employee in data_state._employees.values()
                if not settings_state.only_active or employee.active
            ]
            self.total_amount_of_employees = len(employees)
            shifts = [
                shift
                for shift in data_state._shifts.values()
                if settings_state._start_date <= shift.date <= settings_state._end_date
            ]
        async with anyio.from_thread.create_task_group() as tg:
            for employee in employees:
                tg.start_soon(
                    self._handle_single_employee,
                    employee,
                    data_state._teams.values(),
                    shifts,
                    settings_state._tolerance,
                )

        if not self.filter_value:
            async with self:
                self.errors_to_show = self._calculated_errors[:]
        else:
            for error_to_show in self._calculated_errors:
                if not self.filter_value or _filter_error(self.filter_value.lower(), error_to_show):
                    async with self:
                        self.errors_to_show.append(error_to_show)
        async with self:
            self.is_loading = False

    @rx.event
    def set_filter_value(self, value: str):
        """Filter employees based on the search value."""
        self.filter_value = value
        self.errors_to_show.clear()
        if not value:
            self.errors_to_show = self._calculated_errors[:]
            return
        for error in self._calculated_errors:
            if _filter_error(value.lower(), error):
                self.errors_to_show.append(error)
            yield

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
    return rx.hstack(
        rx.hstack(  # Group "Start date" and its input
            rx.text('Start date'),
            rx.input(
                type='date',
                name='start_date',
                value=SettingsState.start_date,
                on_change=SettingsState.set_start_date,
            ),
            align='center',
            spacing='1',
            min_width='max-content',
        ),
        rx.hstack(  # Group "End date" and its input
            rx.text('End date'),
            rx.input(
                type='date',
                name='end_date',
                value=SettingsState.end_date,
                on_change=SettingsState.set_end_date,
            ),
            align='center',
            spacing='1',
            min_width='max-content',
        ),
        rx.hstack(
            rx.text('Only active'),
            rx.checkbox(default_checked=SettingsState.only_active, on_change=SettingsState.set_only_active),
            align='center',
            min_width='max-content',
            spacing='1',
        ),
        rx.hstack(
            rx.text('Tolerance'),
            rx.input(
                placeholder='Minutes',
                type='number',
                value=SettingsState.tolerance,
                on_change=SettingsState.set_tolerance,
                width='100%',
                regex=r'^\d*$',
                min=0,
            ),
            align='center',
            spacing='1',
            min_width='max-content',
        ),
        rx.cond(
            SettingsState.date_error,
            rx.tooltip(
                rx.button('Submit', disabled=True),
                content='End date must be after start date.',
            ),
            rx.button(
                'Submit',
                loading=DataStateDeprecated.is_loading,
                on_click=DataStateDeprecated.calculate_errors,
            ),
        ),
        spacing='3',
        align='center',
        width='100%',
    )


def render_export_buttons() -> rx.Component:
    """Render the export buttons."""
    return rx.hstack(
        rx.button(
            'Export Selected',
            disabled=DataStateDeprecated.selected_error_ids.length() == 0,
            on_click=DataStateDeprecated.download_selected_errors,
        ),
        rx.button(
            'Export All',
            disabled=DataStateDeprecated.errors_to_show.length() == 0,
            on_click=DataStateDeprecated.download_all_errors,
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
            value=DataStateDeprecated.filter_value,
            on_change=DataStateDeprecated.set_filter_value,
            width='100%',
            placeholder='Filter by name or team',
            disabled=DataStateDeprecated.is_loading,
        ),
        width='50%',
        align='center',
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
        on_click=lambda: DataStateDeprecated.select_row(index),
        background_color=rx.cond(
            DataStateDeprecated.selected_error_ids.contains(index), rx.color('blue', 3), 'transparent'
        ),
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
                DataStateDeprecated.errors_to_show,
                show_employee,
            )
        ),
        width='100%',
    )


def live_progress() -> rx.Component:
    """Show a live progress bar when loading data."""
    return rx.cond(
        ~DataStateDeprecated.is_loading,
        rx.fragment(),
        rx.progress(
            value=DataStateDeprecated.processed_employees,
            max=DataStateDeprecated.total_amount_of_employees,
        ),
    )


@components.requires_authentication
@templates.template
def working_time_verification_page() -> rx.Component:
    """Index page of the app."""
    return rx.vstack(
        rx.hstack(render_input(), render_export_buttons(), render_search(), justify='between', width='100%'),
        live_progress(),
        render_table(),
        width='100%',
    )
