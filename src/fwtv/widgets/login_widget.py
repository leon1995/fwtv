from PySide6.QtCore import QDate
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QWidget

from fwtv.widgets import settings_widget


class LoginWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qh = QHBoxLayout(self)

        self.fetch_data_label = QLabel("Fetch data", self)
        self.fetch_data_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.qh.addWidget(self.fetch_data_label)

        # defaults to fetching data from the last 2 months in order to not fetch entire data history
        self.start_picker = settings_widget.DateSettingWidget("From", QDate.currentDate().addMonths(-2), self)
        self.qh.addWidget(self.start_picker)

        self.end_picker = settings_widget.DateSettingWidget("Until", QDate.currentDate(), self)
        self.qh.addWidget(self.end_picker)

        self.label = QLabel("Enter api key", self)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.qh.addWidget(self.label)

        self.key = QLineEdit(self)
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.qh.addWidget(self.key)

        self.button = QPushButton("Fetch data", self)
        self.button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.qh.addWidget(self.button)

        self.timeout = settings_widget.IntegerPickerWidget("Timeout", 5)
        self.qh.addWidget(self.timeout)

        self.setLayout(self.qh)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Return:
            self.button.clicked.emit()
