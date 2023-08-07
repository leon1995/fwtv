import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget
from factorialhr import endpoints

import fwtv
from fwtv.objects import async_converter
from fwtv.widgets import login_widget
from fwtv.widgets import working_time_widget


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(f"Factorial working time verification - version {fwtv.__version__}")
        self.qv = QVBoxLayout()
        self.login = login_widget.LoginWidget(self)
        self.qv.addWidget(self.login)

        self.verification_widget = working_time_widget.WorkingTimeWidget(self)
        self.qv.addWidget(self.verification_widget)

        self.setLayout(self.qv)

        self.login.button.clicked.connect(async_converter.ToAsync(self.fetch_data))

    async def fetch_data(self):
        self.login.button.hide()
        async with endpoints.NetworkHandler(self.login.key.text()) as api:
            try:
                _attendances = await endpoints.AttendanceEndpoint(api).all()
                _employees = await endpoints.EmployeesEndpoint(api).all()
                _teams = await endpoints.TeamsEndpoint(api).all()
            except Exception as e:
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Icon.Critical)
                message_box.setText(f"{type(e).__name__}\n{e}")
                message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                message_box.setDefaultButton(QMessageBox.StandardButton.Ok)
                message_box.exec()
                return
            finally:
                self.login.button.show()
        self.verification_widget.set_data(_teams, _attendances, _employees)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 675)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
