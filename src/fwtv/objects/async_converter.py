import traceback
import typing

import outcome
import trio
from PySide6.QtCore import QEvent
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication


class ToAsync(QObject):
    class ReenterQtObject(QObject):
        def event(self, event):
            if event.type() == QEvent.User + 1:
                event.fn()
                return True
            return False

    class ReenterQtEvent(QEvent):
        def __init__(self, fn):
            super().__init__(QEvent.Type(QEvent.User + 1))
            self.fn = fn

    def __init__(self, signal: typing.Callable):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = signal

    def __call__(self, *args, **kwargs):
        trio.lowlevel.start_guest_run(
            self.entry,
            *args,
            run_sync_soon_threadsafe=self.next_guest_run_schedule,
            done_callback=self.trio_done_callback,
        )

    def next_guest_run_schedule(self, fn):
        QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(fn))

    @staticmethod
    def trio_done_callback(outcome_):
        if isinstance(outcome_, outcome.Error):
            error = outcome_.error
            traceback.print_exception(type(error), error, error.__traceback__)
