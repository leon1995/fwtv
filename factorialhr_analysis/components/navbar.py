"""The navigation bar component."""

import reflex as rx
from reflex.style import color_mode, set_color_mode

from factorialhr_analysis import routes, states


class NavbarState(rx.State):
    """State for the navigation bar."""

    @rx.event
    async def logout(self):
        """Log out the user."""
        yield [states.OAuthSessionState.delete_session, states.DataState.clear, rx.redirect(routes.INDEX)]


def dark_mode_toggle() -> rx.Component:
    """Toggle for dark/light mode."""
    return rx.segmented_control.root(
        rx.segmented_control.item(
            rx.icon(tag='monitor'),
            value='system',
        ),
        rx.segmented_control.item(
            rx.icon(tag='sun'),
            value='light',
        ),
        rx.segmented_control.item(
            rx.icon(tag='moon'),
            value='dark',
        ),
        on_change=set_color_mode,
        value=color_mode,
    )


def navbar_link(text: str, url: str) -> rx.Component:
    """Link in the navigation bar."""
    return rx.link(rx.text(text, size='4', weight='medium'), href=url)


def refresh_data():
    return rx.hstack(
        rx.button(
            rx.icon('refresh-ccw'),
            on_click=states.DataState.refresh_data,
            loading=states.DataState.is_loading,
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


def icon_menu():
    return (
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
                    rx.link(
                        rx.text('Log out'),
                        href=routes.INDEX,
                        on_click=NavbarState.logout,
                    )
                ),
            ),
            justify='end',
        ),
    )


def navbar() -> rx.Component:
    """Navigation bar component."""
    return rx.box(
        rx.desktop_only(
            rx.hstack(
                rx.hstack(
                    rx.link(rx.heading('Working time analysis', size='5', weight='bold'), href=routes.INDEX),
                    navbar_link('Verification', '/verification'),
                    navbar_link('Projects', '/projects'),
                    align_items='center',
                ),
                rx.hstack(
                    refresh_data(),
                    rx.spacer(),
                    icon_menu(),
                    dark_mode_toggle(),
                    justify='between',
                ),
                justify='between',
                align_items='center',
            ),
        ),
        bg=rx.color('accent', 3),
        padding='1em',
        top='0',
    )
