"""Module for working time widgets."""

import collections
import datetime
import typing

import factorialhr
from PySide6.QtWidgets import QVBoxLayout, QWidget

from fwtv import verifier
from fwtv.widgets import settings_widget, table_widget


def get_errors(
    start: datetime.date,
    end: datetime.date,
    attendances: list[factorialhr.Shift],
    employees: list[factorialhr.Employee],
    tolerance: int,
) -> tuple[dict[str, list[str]], dict[str, list[verifier.Error]]]:
    """Get all errors found."""
    preconditions: dict[str, list[str]] = collections.defaultdict(list)
    employee_errors: dict[str, list[verifier.Error]] = collections.defaultdict(list)
    for employee in employees:
        name = employee.full_name
        employee_attendances: list[verifier.Attendance] = []

        for attendance in filter(lambda x: x.employee_id == employee.id, attendances):
            attendance: factorialhr.Shift
            if not attendance.clock_in:
                preconditions[name].append(f'no clock in time provided for attendance with id "{attendance.id}"')
                continue
            if attendance.date < start or attendance.date > end:
                continue
            if not attendance.clock_out:
                preconditions[name].append(f'no clock out time provided for clock in time "{attendance.clock_in}"')
                continue
            if not attendance.workable:
                continue  # it has been declared as a break
            try:
                # automated time tracking is not precise enough and also is not able to handle seconds precise enough
                a = verifier.Attendance(
                    clock_in=datetime.datetime.combine(attendance.date, attendance.clock_in.replace(second=0)),
                    clock_out=datetime.datetime.combine(attendance.date, attendance.clock_out.replace(second=0)),
                )
                employee_attendances.append(a)
            except ValueError as e:
                preconditions[name].append(str(e))
                continue

        errors = verifier.verify_attendances(employee_attendances, datetime.timedelta(minutes=tolerance))
        if errors:
            employee_errors[name] = errors
    return preconditions, employee_errors


class WorkingTimeWidget(QWidget):
    """Widget to display working times."""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.teams = []
        self.attendances = []
        self.employees_by_team = {}
        self.employees = []
        self.qv = QVBoxLayout(self)

        self.settings_widget = settings_widget.SettingsWidget(self)
        self.qv.addWidget(self.settings_widget)

        self.preconditions_table = table_widget.PreconditionErrorsTableWidget(self)
        self.qv.addWidget(self.preconditions_table)

        self.failures_table = table_widget.FailuresTableWidget(self)
        self.qv.addWidget(self.failures_table)

        self.setLayout(self.qv)

        self.settings_widget.team_selector.selector.currentIndexChanged.connect(self.update_data)
        self.settings_widget.start_picker.date.dateChanged.connect(self.update_data)
        self.settings_widget.end_picker.date.dateChanged.connect(self.update_data)
        self.settings_widget.tolerance_selector.picker.valueChanged.connect(self.update_data)

        self.update_data()

    def set_data(
        self,
        teams: list[factorialhr.Team],
        attendances: list[factorialhr.Shift],
        employees: list[factorialhr.Employee],
    ):
        """Fetch new data and update tables."""
        self.attendances = attendances
        self.teams = teams
        self.employees = employees
        self.employees_by_team = {
            t.id: [e for e in employees if t.employee_ids and e.id in t.employee_ids] for t in teams
        }
        for i in range(self.settings_widget.team_selector.selector.count()):
            self.settings_widget.team_selector.selector.removeItem(i)
        self.settings_widget.team_selector.selector.addItems([team.name for team in teams])
        self.settings_widget.team_selector.selector.addItems([employee.full_name for employee in employees])
        self.update_data()

    def get_current_selection(self) -> factorialhr.Team | factorialhr.Employee | None:
        """Get current selection of teams."""
        index = self.settings_widget.team_selector.selector.currentIndex()
        if 0 <= index < len(self.teams):
            return self.teams[index]
        if 0 <= (index := index - len(self.teams)) < len(self.employees):
            return self.employees[index]
        return None

    def update_data(self):
        """Update the data and populate new data into tables."""
        selection = self.get_current_selection()
        employees = []
        if isinstance(selection, factorialhr.Team):
            employees = self.employees_by_team[selection.id]
        elif isinstance(selection, factorialhr.Employee):
            employees = [selection]

        preconditions, errors = get_errors(
            typing.cast(
                datetime.date,
                self.settings_widget.start_picker.date.date().toPython(),
            ),
            typing.cast(
                datetime.date,
                self.settings_widget.end_picker.date.date().toPython(),
            ),
            self.attendances,
            employees,
            self.settings_widget.tolerance_selector.value(),
        )
        entries = collections.defaultdict(list)
        for k in preconditions:
            entries[k] = [preconditions[k]]
        self.preconditions_table.set_data(entries)
        self.failures_table.set_data(errors)
