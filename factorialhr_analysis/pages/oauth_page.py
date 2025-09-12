import functools
import logging
import secrets
import urllib.parse
from collections.abc import Callable

import httpx
import reflex as rx

from factorialhr_analysis import constants, states


class OAuthProcessState(rx.State):
    """State to handle OAuth token processing."""

    error: rx.Field[str | None] = rx.field(default=None)
    expected_state: rx.Field[str | None] = rx.field(default=None)

    @rx.event
    async def start_oauth_process(self):
        """Redirect to the OAuth authorization URL."""
        if not self.expected_state:
            self.expected_state = secrets.token_urlsafe(16)
        auth_url = (
            f'{constants.ENVIRONMENT_URL}/oauth/authorize?'
            f'response_type=code&'
            f'client_id={constants.CLIENT_ID}&'
            f'redirect_uri={urllib.parse.quote(constants.REDIRECT_URI)}&'
            f'scope={constants.SCOPE}&'
            f'state={self.expected_state}'
        )
        yield rx.redirect(auth_url)

    @rx.event
    async def process_oauth_response(self):
        """Process the OAuth response to exchange code for an access token."""
        expected_state = self.router.url.query_parameters.get('state')
        if not expected_state:
            self.error = 'State is missing.'
            self.expected_state = None
            return
        if self.expected_state != expected_state:
            self.error = f'State mismatch error. Expected {self.expected_state} but got {expected_state}.'
            self.expected_state = None
            return
        code = self.router.url.query_parameters.get('code')
        if not code:
            self.error = 'Authorization code is missing.'
            self.expected_state = None
            return
        oauth_session = await self.get_state(states.OAuthSessionState)
        try:
            await oauth_session.create_session(code, grant_type='authorization_code')
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logging.getLogger(__name__).exception('error creating oauth session')
            self.error = str(e)
        else:
            logging.getLogger(__name__).info('created oauth session')
            yield states.DataState.refresh_data
        finally:
            self.error = ''
            self.expected_state = ''


def redirect_if_authenticated(page: Callable[[], rx.Component]) -> Callable[[], rx.Component]:
    """Redirect authenticated users away from login page."""

    @functools.wraps(page)
    def login_page_wrapper() -> rx.Component:
        return rx.cond(
            states.OAuthSessionState.is_hydrated,
            rx.cond(
                states.OAuthSessionState.is_session_authenticated,
                rx.fragment(on_mount=states.OAuthSessionState.redir),
                page(),
            ),
            rx.spinner(),
        )

    return login_page_wrapper


@redirect_if_authenticated
def start_oauth_process():
    return rx.text('Redirecting to factorialhr...', on_mount=OAuthProcessState.start_oauth_process)


@redirect_if_authenticated
def authorize_oauth_page():
    return rx.box(
        rx.text('Validating response...'),
        rx.text(OAuthProcessState.error, color='red'),
        on_mount=OAuthProcessState.process_oauth_response,
    )
