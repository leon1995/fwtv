"""The navigation bar component."""

import reflex as rx
from reflex.style import color_mode, set_color_mode

from factorialhr_analysis import routes, state


def dark_mode_toggle() -> rx.Component:
    """Toggle for dark/light mode."""
    return rx.segmented_control.root(
        rx.segmented_control.item(
            rx.icon(tag='monitor', size=20),
            value='system',
        ),
        rx.segmented_control.item(
            rx.icon(tag='sun', size=20),
            value='light',
        ),
        rx.segmented_control.item(
            rx.icon(tag='moon', size=20),
            value='dark',
        ),
        on_change=set_color_mode,
        variant='classic',
        radius='large',
        value=color_mode,
    )


def navbar_link(text: str, url: str) -> rx.Component:
    """Link in the navigation bar."""
    return rx.link(rx.text(text, size='4', weight='medium'), href=url)


def navbar() -> rx.Component:
    """Navigation bar component."""
    return rx.box(
        rx.desktop_only(
            rx.hstack(
                rx.heading('Factorialhr analysis', size='7', weight='bold'),
                rx.hstack(
                    navbar_link('Working time verification', '/#'),
                    spacing='5',
                ),
                rx.hstack(
                    rx.menu.root(
                        rx.menu.trigger(
                            rx.icon_button(
                                rx.icon('user'),
                                size='2',
                                radius='full',
                            )
                        ),
                        rx.menu.content(
                            rx.menu.item(
                                rx.link(rx.text('Log out'), href=routes.INDEX, on_click=state.LoginState.logout)
                            ),
                        ),
                        justify='end',
                    ),
                    dark_mode_toggle(),
                ),
                justify='between',
                align_items='center',
            ),
        ),
        bg=rx.color('accent', 3),
        padding='1em',
        width='100%',
    )
