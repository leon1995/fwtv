from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QDateEdit
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


class SettingsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.team_selector = TeamOrEmployeeSettingWidget(self)
        self.qh.addWidget(self.team_selector)

        self.start_picker = DateSettingWidget("Start on", QDate.currentDate().addMonths(-1), self)
        self.qh.addWidget(self.start_picker)

        self.end_picker = DateSettingWidget("End on", QDate.currentDate(), self)
        self.qh.addWidget(self.end_picker)

        self.setLayout(self.qh)
