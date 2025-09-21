"""Footer component."""

import reflex as rx

from factorialhr_analysis import states


def refresh_data() -> rx.Component:
    """Refresh data button."""
    return rx.hstack(
        rx.button(
            rx.icon('refresh-ccw'),
            on_click=states.DataState.refresh_data,
            loading=states.DataState.is_loading,
            border_radius='1em',
        ),
        rx.text(
            'Last data update: ',
            rx.cond(
                states.DataState.last_updated.is_not_none(),
                rx.moment(states.DataState.last_updated, from_now=True),
                'Never',
            ),
        ),
        align='center',
    )


def footer() -> rx.Component:
    """Footer component."""
    return rx.el.footer(
        refresh_data(),
        position='fixed',
        padding='0.5em',
        bottom='0',
        width='100%',
        bg=rx.color('gray', 3),
    )
