"""A date range selector component using Reflex framework."""

import reflex as rx


class DateRangeState(rx.State):
    """State for the date range picker component."""

    start_date: str = ''
    end_date: str = ''
    temp_start_date: str = ''
    temp_end_date: str = ''

    @rx.event
    def apply_date_range(self):
        """Apply the selected date range."""
        self.start_date = self.temp_start_date
        self.end_date = self.temp_end_date


def date_range_picker() -> rx.Component:
    """Date range picker component."""
    return rx.dialog.root(
        rx.dialog.trigger(rx.button('Select Date Range')),
        rx.dialog.content(
            rx.dialog.title('Select Date Range'),
            rx.dialog.description('Choose start and end dates'),
            rx.vstack(
                rx.text('Start Date:'),
                rx.input(
                    type='date', value=DateRangeState.temp_start_date, on_change=DateRangeState.set_temp_start_date
                ),
                rx.text('End Date:'),
                rx.input(type='date', value=DateRangeState.temp_end_date, on_change=DateRangeState.set_temp_end_date),
                rx.flex(
                    rx.dialog.close(rx.button('Cancel')),
                    rx.dialog.close(rx.button('Apply', on_click=DateRangeState.apply_date_range)),
                    spacing='3',
                    justify='end',
                ),
                spacing='4',
            ),
        ),
    )


def date_inputs() -> rx.Component:
    """Display the selected date range in read-only input fields."""
    return rx.hstack(
        rx.input(placeholder='Start Date', value=DateRangeState.start_date, read_only=True),
        rx.input(placeholder='End Date', value=DateRangeState.end_date, read_only=True),
        spacing='2',
    )
