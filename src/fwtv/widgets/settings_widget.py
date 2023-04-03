from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QDateEdit
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QWidget


class TeamSettingWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel("Select a team", self)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.qh.addWidget(self.label)

        self.selector = QComboBox(self)
        self.qh.addWidget(self.selector)

        self.setLayout(self.qh)


class DateSettingWidget(QWidget):
    def __init__(self, label: str, date: QDate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)
        self.label = QLabel(label, self)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
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
        self.team_selector = TeamSettingWidget(self)
        self.qh.addWidget(self.team_selector)

        self.start_picker = DateSettingWidget("Start on", QDate.currentDate().addMonths(-1), self)
        self.qh.addWidget(self.start_picker)

        self.end_picker = DateSettingWidget("End on", QDate.currentDate(), self)
        self.qh.addWidget(self.end_picker)

        self.setLayout(self.qh)
