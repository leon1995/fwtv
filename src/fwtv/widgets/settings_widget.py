"""Module for setting widgets."""

import typing

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)


class TeamOrEmployeeSettingWidget(QWidget):
    """A widget to select a team or employee."""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel('Select a team or an employee', self)
        self.qh.addWidget(self.label)

        self.selector = QComboBox(self)
        self.selector.setEditable(True)
        self.selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.qh.addWidget(self.selector)

        self.setLayout(self.qh)


class DateSettingWidget(QWidget):
    """A picker for dates."""

    def __init__(self, label: str, date: QDate, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel(label, self)
        self.qh.addWidget(self.label)

        self.date = QDateEdit(date, self)
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat('yyyy-MM-dd')
        self.qh.addWidget(self.date)

        self.setLayout(self.qh)


class IntegerPickerWidget(QWidget):
    """A picker for integers."""

    def __init__(self, label: str, default: int, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel(label, self)
        self.qh.addWidget(self.label)

        self.picker = QDoubleSpinBox(self, maximum=999)  # allow maximum of 9-digit number
        self.picker.setSingleStep(1)
        self.picker.setDecimals(0)
        self.picker.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.picker.setValue(default)
        self.qh.addWidget(self.picker)

        self.setLayout(self.qh)

    def value(self) -> int:
        """Get the value of the integer picker."""
        return int(self.picker.value())


class SettingsWidget(QWidget):
    """Provide some settings for the user."""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.team_selector = TeamOrEmployeeSettingWidget(self)
        self.qh.addWidget(self.team_selector)

        last_month = QDate.currentDate().addMonths(-1)
        self.start_picker = DateSettingWidget('Start on', QDate(last_month.year(), last_month.month(), 1), self)
        self.qh.addWidget(self.start_picker)

        self.end_picker = DateSettingWidget(
            'End on',
            QDate(last_month.year(), last_month.month(), last_month.daysInMonth()).addDays(1),
            self,
        )
        self.qh.addWidget(self.end_picker)

        self.tolerance_selector = IntegerPickerWidget('Tolerance', 1)
        self.qh.addWidget(self.tolerance_selector)

        self.setLayout(self.qh)
