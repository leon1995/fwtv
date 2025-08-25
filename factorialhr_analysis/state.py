"""Login state."""

import functools
import logging
import os
import time
import typing

import factorialhr
import httpx
import pydantic
import reflex as rx

from factorialhr_analysis import routes

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class ApiSession(pydantic.BaseModel):
    """Wrapper class for the API session cookie."""

    access_token: str
    refresh_token: str
    created_at: int
    token_type: str

    def access_token_expiration(self) -> int:
        """Get the expiration date of the access token."""
        return self.created_at + 60 * 60  # access token is valid for 1 hour

    def is_access_token_expired(self) -> bool:
        """Determine whether the access token is expired or not."""
        return self.access_token_expiration() <= time.time()

    def refresh_token_expiration(self) -> int:
        """Get the expiration date of the refresh token."""
        return self.created_at + 7 * 24 * 60 * 60  # refresh token is valid for 1 week

    def is_refresh_token_expired(self) -> bool:
        """Determine whether the refresh token is expired or not."""
        return self.refresh_token_expiration() <= time.time()


class LoginState(rx.State):
    """State for managing login and authentication."""

    api_session_cookie: str = rx.Cookie(
        name='api_session',
        same_site='strict',
    )
    redirect_to: str = ''

    def get_auth(self) -> factorialhr.AccessTokenAuth | factorialhr.ApiKeyAuth:
        """Get the authentication object for the API session."""
        if api_token := os.environ.get('FACTORIALHR_API_KEY'):
            return factorialhr.ApiKeyAuth(api_key=api_token)
        api_session = self.api_session()
        if api_session is None:
            msg = 'api_session_cookie must be valid'
            raise RuntimeError(msg)
        return factorialhr.AccessTokenAuth(
            access_token=api_session.access_token,
            token_type=api_session.token_type,
        )

    def api_session(self) -> ApiSession | None:
        """Get the API session from the cookie."""
        if not self.api_session_cookie:
            return None
        try:
            return ApiSession.model_validate_json(self.api_session_cookie)
        except pydantic.ValidationError as e:
            logger.exception('parsing cookie failed', exc_info=e)
            return None

    @rx.event
    async def login(self, token: str, *, grant_type: typing.Literal['refresh_token', 'authorization_code']) -> None:
        """Log in to the API and store the session cookie."""
        if grant_type == 'refresh_token':
            data = {
                'client_id': os.environ['FACTORIALHR_CLIENT_ID'],
                'client_secret': os.environ['FACTORIALHR_CLIENT_SECRET'],
                'grant_type': 'refresh_token',
                'refresh_token': token,
            }
        else:
            data = {
                'client_id': os.environ['FACTORIALHR_CLIENT_ID'],
                'client_secret': os.environ['FACTORIALHR_CLIENT_SECRET'],
                'code': token,
                'grant_type': 'authorization_code',
                'redirect_uri': os.environ['FACTORIALHR_REDIRECT_URI'],
            }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    os.environ['FACTORIALHR_ENVIRONMENT_URL'] + '/oauth/token',
                    data=data,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception('Login failed', exc_info=e)
            raise
        else:
            self.api_session_cookie = ApiSession(**response.json()).model_dump_json()
            logger.info('Refreshed access token')

    @rx.var(cache=False)
    async def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        if os.environ.get('FACTORIALHR_API_KEY'):
            return True  # If using API key, always authenticated
        api_session = self.api_session()
        if api_session is None:
            return False
        return not api_session.is_access_token_expired()

    @rx.event
    async def refresh(self) -> bool:
        """Check if the user is authenticated."""
        if not self.is_hydrated:
            return False
        api_session = self.api_session()
        if api_session is None:
            return False
        if api_session.is_refresh_token_expired():
            return False
        if api_session.is_access_token_expired():
            try:
                await self.login(token=api_session.refresh_token, grant_type='refresh_token')
            except httpx.HTTPStatusError:
                return False
        return True

    @rx.event
    async def redir(self):
        """Redirect to the redirect_to route if logged in, or to the login page if not."""
        if not self.is_hydrated:
            yield self.redir()
        page = self.router.url.path
        is_authenticated = await self.is_authenticated
        if not is_authenticated:
            is_authenticated = await self.refresh()
        if not is_authenticated:
            self.redirect_to = page
            return_value = []
            if not self.api_session_cookie:
                return_value.append(rx.remove_cookie('api_session'))
            if page != routes.LOGIN_ROUTE:
                yield [*return_value, rx.redirect(routes.LOGIN_ROUTE)]
        if is_authenticated and page == routes.LOGIN_ROUTE:
            yield rx.redirect(self.redirect_to or '/')

    @rx.event
    def logout(self):
        """Log out the user."""
        yield [rx.remove_cookie('api_session'), rx.redirect(routes.LOGIN_ROUTE)]


def redirect_for_login(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Require authentication before rendering a page.

    If the user is not authenticated, then redirect to the login page.
    """

    @functools.wraps(page)
    def protected_page() -> rx.Component:
        return rx.fragment(
            rx.cond(
                LoginState.is_hydrated,
                rx.cond(
                    LoginState.is_authenticated,
                    page(),
                    rx.spinner(on_mount=LoginState.redir),
                ),
                rx.spinner(),  # Show spinner while hydrating
            )
        )

    return protected_page
