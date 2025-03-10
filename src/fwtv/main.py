"""Entrypoint and main window of the application."""

import datetime
import sys
import typing

import factorialhr
from PySide6.QtWidgets import QApplication, QMessageBox, QVBoxLayout, QWidget

import fwtv
from fwtv.objects import async_converter
from fwtv.widgets import login_widget, working_time_widget


class MainWindow(QWidget):
    """Main window widget."""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(f'Factorial working time verification - version {fwtv.__version__}')
        self.qv = QVBoxLayout()
        self.login = login_widget.LoginWidget(self)
        self.qv.addWidget(self.login)

        self.verification_widget = working_time_widget.WorkingTimeWidget(self)
        self.qv.addWidget(self.verification_widget)

        self.setLayout(self.qv)

        self.login.button.clicked.connect(async_converter.ToAsync(self.fetch_data))

    async def fetch_data(self):
        """Fetch data from the api."""
        self.login.button.hide()
        async with factorialhr.ApiClient(auth=factorialhr.ApiKeyAuth(self.login.key.text())) as api:
            try:
                _attendances = await factorialhr.ShiftEndpoint(api).all(
                    start_on=typing.cast(
                        datetime.date | None,
                        self.login.start_picker.date.date().toPython(),
                    ),
                    end_on=typing.cast(
                        datetime.date | None,
                        self.login.end_picker.date.date().toPython(),
                    ),
                    timeout=self.login.timeout.value(),
                )
                _employees = await factorialhr.EmployeeEndpoint(api).all()
                _teams = await factorialhr.TeamEndpoint(api).all()
            except Exception as e:  # noqa: BLE001
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Icon.Critical)
                message_box.setText(f'{type(e).__name__}\n{e}')
                message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                message_box.setDefaultButton(QMessageBox.StandardButton.Ok)
                message_box.exec()
                return
            finally:
                self.login.button.show()
        self.verification_widget.set_data(_teams, _attendances, _employees)


def main() -> int:
    """Entrypoint for application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 675)
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
