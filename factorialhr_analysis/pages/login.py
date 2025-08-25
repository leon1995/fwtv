"""Login page."""

import functools
import typing

import httpx
import reflex as rx

from factorialhr_analysis import routes, state, templates


class LoginFormState(rx.State):
    """State for the login form."""

    user_entered_authorization_code: str
    auth_code_invalid: bool = False
    auth_code_invalid_message: str

    @rx.var
    def authorization_code_empty(self) -> bool:
        """Check if the authorization code input is empty."""
        return not self.user_entered_authorization_code.strip()

    @rx.var
    def authorization_invalid(self) -> bool:
        """Check if the authorization code is invalid."""
        return self.auth_code_invalid

    @rx.var
    def authorization_code_invalid_message(self) -> str:
        """Get the authorization code invalid message."""
        return self.auth_code_invalid_message

    @rx.event
    async def handle_submit(self, form_data: dict[str, typing.Any]):
        """Handle form submission."""
        self.auth_code_invalid = False
        login_state = await self.get_state(state.LoginState)
        try:
            await login_state.login(form_data.get('authorization_code'), grant_type='authorization_code')
            yield rx.redirect(routes.INDEX)
        except httpx.HTTPStatusError as e:
            self.auth_code_invalid = True
            self.auth_code_invalid_message = f'Login failed with status code: {e.response.status_code}'


def authorization_code_form() -> rx.Component:
    """Form for the authorization code input."""
    return rx.form.root(
        rx.form.field(
            rx.vstack(
                rx.form.label(
                    'Authorization Code',
                    size='3',
                    weight='medium',
                    text_align='left',
                    width='100%',
                ),
                rx.form.control(
                    rx.input(
                        name='authorization_code',
                        size='3',
                        width='100%',
                        on_change=LoginFormState.set_user_entered_authorization_code,
                    ),
                    as_child=True,
                ),
                rx.cond(
                    LoginFormState.authorization_invalid,
                    rx.form.message(
                        LoginFormState.authorization_code_invalid_message,
                        color='var(--red-11)',
                    ),
                ),
                rx.button(
                    'Sign in', size='2', width='100%', type='submit', disabled=LoginFormState.authorization_code_empty
                ),
                spacing='2',
                width='100%',
            ),
            name='authorization_code',
            server_invalid=LoginFormState.auth_code_invalid,
        ),
        on_submit=LoginFormState.handle_submit,
        reset_on_submit=True,
    )


def redirect_if_authenticated(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Redirect authenticated users away from login page."""

    @functools.wraps(page)
    def login_page_wrapper() -> rx.Component:
        return rx.cond(
            state.LoginState.is_hydrated,
            rx.cond(
                state.LoginState.is_authenticated,
                rx.spinner(on_mount=state.LoginState.redir),
                page(),  # Show login form if not authenticated
            ),
            rx.spinner(),
        )

    return login_page_wrapper


@templates.template
@redirect_if_authenticated
def login_page() -> rx.Component:
    """Login page."""
    return rx.center(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.heading(
                        'Login to FactorialHR',
                        size='6',
                        as_='h2',
                        text_align='center',
                        width='100%',
                    ),
                    direction='column',
                    spacing='5',
                    width='100%',
                ),
                authorization_code_form(),
            ),
            size='4',
            max_width='28em',
            width='100%',
        ),
        height='100vh',
    )
