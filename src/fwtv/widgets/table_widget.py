import collections

import tabulate
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHeaderView
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QTableView
from PySide6.QtWidgets import QTableWidget
from PySide6.QtWidgets import QTableWidgetItem


class ErrorTable(QTableWidget):
    def __init__(self, labels: list[str], *args, **kwargs):
        self.labels = labels
        super().__init__(0, len(self.labels), *args, **kwargs)
        self.setHorizontalHeaderLabels(self.labels)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.set_data({})

    def set_data(self, data: dict[str, list[list[str]]]):
        self.setSortingEnabled(False)
        self.setRowCount(sum(len(failures) for failures in data.values()))
        row_index = 0
        for name, errors in data.items():
            for i, error in enumerate(errors):
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
        super().set_data(data)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        if not any(data) and not self.isHidden():
            self.hide()
        elif any(data) and self.isHidden():
            self.show()


class FailuresTableWidget(ErrorTable):
    def __init__(self, *args, **kwargs):
        super().__init__(["Name", "Day(s)", "Reason", "Break", "Attended"], *args, **kwargs)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: dict[str, list[list[str]]]):
        super().set_data(data)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
