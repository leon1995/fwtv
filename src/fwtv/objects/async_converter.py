"""A wrapper to call async functions.

Taken from https://doc.qt.io/qtforpython-6.5/examples/example_async_minimal.html
"""

import traceback
import typing

import outcome
import trio
from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication


class ToAsync(QObject):  # noqa: D101
    class ReenterQtObject(QObject):
        """This is a QObject to which an event will be posted, allowing Trio to resume when the event is handled.

        event.fn() is the next entry point of the Trio event loop.
        """  # noqa: D404

        def event(self, event) -> bool:  # noqa: ANN001, D102
            if event.type() == QEvent.User + 1:  # pyright: ignore [reportAttributeAccessIssue]
                event.fn()
                return True
            return False

    class ReenterQtEvent(QEvent):
        """This is the QEvent that will be handled by the ReenterQtObject.

        self.fn is the next entry point of the Trio event loop.
        """  # noqa: D404

        def __init__(self, fn):  # noqa: ANN001
            super().__init__(QEvent.Type(QEvent.User + 1))  # pyright: ignore [reportAttributeAccessIssue]
            self.fn = fn

    def __init__(self, signal: typing.Callable):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = signal

    def __call__(self, *args, **kwargs):  # noqa: ANN003, ANN002, D102, ARG002
        trio.lowlevel.start_guest_run(
            self.entry,
            *args,
            run_sync_soon_threadsafe=self.next_guest_run_schedule,
            done_callback=self.trio_done_callback,
        )

    def next_guest_run_schedule(self, fn):  # noqa: ANN001
        """This function serves to re-schedule the guest (Trio) event loop inside the host (Qt) event loop.

        It is called by Trio at the end of an event loop run in order to relinquish back to Qt's event loop.
        By posting an event on the Qt event loop that contains Trio's next entry point, it ensures that Trio's
        event loop will be scheduled again by Qt.
        """  # noqa: D401, D404
        QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(fn))

    def trio_done_callback(self, outcome_):  # noqa: ANN001
        """This function is called by Trio when its event loop has finished."""  # noqa: D401, D404
        if isinstance(outcome_, outcome.Error):
            error = outcome_.error
            traceback.print_exception(type(error), error, error.__traceback__)
