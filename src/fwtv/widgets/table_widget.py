import collections

import tabulate
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHeaderView
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QTableView
from PySide6.QtWidgets import QTableWidget
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from fwtv import verifier


class ErrorTable(QTableWidget):
    def __init__(self, labels: list[str], *args, **kwargs):
        self.labels = labels
        super().__init__(0, len(self.labels), *args, **kwargs)
        self.setHorizontalHeaderLabels(self.labels)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._set_data({})

    def _set_data(self, data: dict[str, list[list[str]]]):
        self.setSortingEnabled(False)
        self.setRowCount(sum(len(failures) for failures in data.values()))
        row_index = 0
        for name, errors in data.items():
            for error in errors:
                self._set_row(row_index, name, *error)
                row_index += 1
        self.horizontalHeader().resizeSections(QHeaderView.ResizeMode.ResizeToContents)
        self.setSortingEnabled(True)

    def _set_row(self, row_index: int, *columns: str):
        for column_index, text in enumerate(columns):
            column_item = QTableWidgetItem(text)
            column_item.setFlags(
                Qt.ItemFlag.ItemNeverHasChildren
                | Qt.ItemFlag.ItemIsAutoTristate
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            self.setItem(row_index, column_index, column_item)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_C and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            row_by_index = collections.defaultdict(list)
            for index in self.selectedIndexes():
                row_by_index[index.row()].append(index.data())
            rows = []
            for row in row_by_index.values():
                rows.append(row)
            table = tabulate.tabulate(rows, headers=self.labels, tablefmt="orgtbl")
            QClipboard().setText(table)


class PreconditionErrorsTableWidget(ErrorTable):
    def __init__(self, *args, **kwargs):
        super().__init__(["Name", "Error"], *args, **kwargs)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def set_data(self, data: dict[str, list[list[str]]]):
        super()._set_data(data)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        if not any(data) and not self.isHidden():
            self.hide()
        elif any(data) and self.isHidden():
            self.show()


class AdditionalInformationWidget(QWidget):
    def __init__(self, name: str, error: verifier.Error, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qv = QVBoxLayout(self)

        self.label = QLabel(name)
        self.qv.addWidget(self.label)

        self.attendances = QTableWidget(len(error.attendances), 2, self)
        for i, a in enumerate(error.attendances):
            column_item = QTableWidgetItem(a.clock_in.strftime("%H:%M"))
            column_item.setFlags(
                Qt.ItemFlag.ItemNeverHasChildren | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsEnabled
            )
            self.attendances.setItem(i, 0, column_item)
            column_item = QTableWidgetItem(a.clock_out.strftime("%H:%M"))
            column_item.setFlags(
                Qt.ItemFlag.ItemNeverHasChildren | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsEnabled
            )
            self.attendances.setItem(i, 1, column_item)
        self.attendances.setHorizontalHeaderLabels(["Clock in", "Clock out"])
        self.attendances.horizontalHeader().resizeSections(QHeaderView.ResizeMode.ResizeToContents)
        self.qv.addWidget(self.attendances)

        self.error = QLabel(error.reason)
        self.qv.addWidget(self.error)

        self.setLayout(self.qv)


class FailuresTableWidget(ErrorTable):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ["Name", "Affected Day(s)", "Reason", "Cumulated Break", "Cumulated Attendance"], *args, **kwargs
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.data: dict[str, list[verifier.Error]] = dict()
        self.cellDoubleClicked.connect(self.display_additional_information)

    def set_data(self, data: dict[str, list[verifier.Error]]):
        self.data = data
        entries = collections.defaultdict(list)
        for name, error in data.items():
            for e in error:
                affected_days = [str(day) for day in e.days_affected]
                affected_days.sort()
                entries[name].append([", ".join(affected_days), e.reason, str(e.break_time), str(e.time_attended)])
        super()._set_data(entries)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def display_additional_information(self, row: int, _: int):
        rows = []
        for name, error in self.data.items():
            for e in error:
                rows.append((name, e))
        self.new_window = AdditionalInformationWidget(rows[row][0], rows[row][1])
        self.new_window.show()
