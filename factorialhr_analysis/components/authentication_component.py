import functools

import reflex as rx

from factorialhr_analysis import states


def requires_authentication(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Require authentication before rendering a page.

    If the user is not authenticated, then redirect to the login page.
    """

    @functools.wraps(page)
    def protected_page() -> rx.Component:
        return rx.fragment(
            rx.cond(
                states.OAuthSessionState.is_hydrated,
                rx.cond(
                    states.OAuthSessionState.is_session_authenticated,
                    page(),
                    rx.spinner(on_mount=states.OAuthSessionState.redir),
                ),
                rx.text('hydrating states...'),
            )
        )

    return protected_page
