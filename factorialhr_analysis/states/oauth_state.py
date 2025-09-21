"""State for managing OAuth session and authentication."""

import os
import time
import typing

import factorialhr
import httpx
import pydantic
import reflex as rx

from factorialhr_analysis import constants, routes


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


class OAuthSessionState(rx.State):
    """State for managing OAuth session and authentication."""

    api_session_cookie: str = rx.Cookie(
        name='api_session',
        same_site='strict',
        secure=os.environ.get('REFLEX_ENV_MODE') == rx.constants.Env.PROD,
        max_age=7 * 24 * 60 * 60,
    )
    _redirect_to: str = ''

    def api_session(self) -> ApiSession | None:
        """Get the API session from the cookie."""
        if not self.api_session_cookie:
            return None
        try:
            return ApiSession.model_validate_json(self.api_session_cookie)
        except pydantic.ValidationError:
            return None

    @rx.event
    async def create_session(self, token: str, grant_type: typing.Literal['refresh_token', 'authorization_code']):
        """Log in to the API and store the session cookie."""
        data = {
            'client_id': constants.CLIENT_ID,
            'client_secret': constants.CLIENT_SECRET,
        }
        if grant_type == 'refresh_token':
            data.update(
                {
                    'grant_type': 'refresh_token',
                    'refresh_token': token,
                }
            )
        else:
            data.update(
                {
                    'code': token,
                    'grant_type': 'authorization_code',
                    'redirect_uri': constants.REDIRECT_URI,
                }
            )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{constants.ENVIRONMENT_URL}/oauth/token',
                data=data,
            )
        response.raise_for_status()
        self.api_session_cookie = ApiSession(**response.json()).model_dump_json()

    @rx.event
    def delete_session(self):
        """Log out the user."""
        yield rx.remove_cookie('api_session')

    @rx.event
    async def refresh_session(self) -> bool:
        """Refresh the access token if it is expired."""
        api_session = self.api_session()
        if api_session is None:
            return False
        if api_session.is_refresh_token_expired():
            return False
        if api_session.is_access_token_expired():
            try:
                await self.create_session(token=api_session.refresh_token, grant_type='refresh_token')
            except (httpx.RequestError, httpx.HTTPError):
                return False
        return True

    @rx.var(cache=False)
    async def is_session_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        if constants.API_KEY:
            return True
        api_session = self.api_session()
        if api_session is None:
            return False
        return not api_session.is_access_token_expired()

    @rx.event
    async def redir(self):
        """Redirect to the redirect_to route if logged in, or to the login page if not."""
        if not self.is_hydrated:
            yield self.redir()
        page = self.router.url.path
        is_authenticated = await self.is_session_authenticated
        if not is_authenticated:
            is_authenticated = await self.refresh_session()
        if not is_authenticated and page != routes.OAUTH_START_ROUTE:
            self._redirect_to = page
            yield rx.redirect(routes.OAUTH_START_ROUTE)
        if is_authenticated and page in (routes.OAUTH_START_ROUTE, routes.OAUTH_AUTHORIZE_ROUTE):
            yield rx.redirect(self._redirect_to or routes.INDEX)

    def get_auth(self) -> factorialhr.AccessTokenAuth | factorialhr.ApiKeyAuth:
        """Get the authentication object for the API session."""
        if constants.API_KEY:
            return factorialhr.ApiKeyAuth(api_key=constants.API_KEY)
        api_session = self.api_session()
        if api_session is None:
            msg = 'api_session_cookie must be valid'
            raise ValueError(msg)
        return factorialhr.AccessTokenAuth(
            access_token=api_session.access_token,
            token_type=api_session.token_type,
        )
