from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QDateEdit
from PySide6.QtWidgets import QDoubleSpinBox
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QWidget


class TeamOrEmployeeSettingWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel("Select a team or an employee", self)
        self.qh.addWidget(self.label)

        self.selector = QComboBox(self)
        self.selector.setEditable(True)
        self.selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.qh.addWidget(self.selector)

        self.setLayout(self.qh)


class DateSettingWidget(QWidget):
    def __init__(self, label: str, date: QDate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel(label, self)
        self.qh.addWidget(self.label)

        self.date = QDateEdit(date, self)
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.qh.addWidget(self.date)

        self.setLayout(self.qh)


class IntegerPickerWidget(QWidget):
    def __init__(self, label: str, default: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel(label, self)
        self.qh.addWidget(self.label)

        self.picker = QDoubleSpinBox(self)
        self.picker.setSingleStep(1)
        self.picker.setDecimals(0)
        self.picker.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.picker.setValue(default)
        self.qh.addWidget(self.picker)

        self.setLayout(self.qh)

    def value(self) -> int:
        return int(self.picker.value())


class SettingsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.team_selector = TeamOrEmployeeSettingWidget(self)
        self.qh.addWidget(self.team_selector)

        last_month = QDate.currentDate().addMonths(-1)
        self.start_picker = DateSettingWidget("Start on", QDate(last_month.year(), last_month.month(), 1), self)
        self.qh.addWidget(self.start_picker)

        self.end_picker = DateSettingWidget(
            "End on", QDate(last_month.year(), last_month.month(), last_month.daysInMonth()).addDays(1), self
        )
        self.qh.addWidget(self.end_picker)

        self.tolerance_selector = IntegerPickerWidget("Tolerance", 1)
        self.qh.addWidget(self.tolerance_selector)

        self.setLayout(self.qh)
