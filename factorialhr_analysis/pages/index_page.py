import logging

import factorialhr
import reflex as rx
from factorialhr_analysis import templates, constants, states


class IndexState(rx.State):
    """State for the index page."""

    @rx.event
    async def get_credentials(self):
        oauth_state = await self.get_state(states.OAuthSessionState)
        async with factorialhr.ApiClient(base_url=constants.ENVIRONMENT_URL, auth=oauth_state.get_auth()) as api_client:
            logging.getLogger(__name__).error(await factorialhr.CredentialsEndpoint(api_client).get())

@templates.template
def index_page() -> rx.Component:
    """The index page of the application."""
    return rx.center(
        rx.vstack(
            rx.heading('Welcome to FactorialHR Analysis', size='4'),
            rx.text('Analyze your FactorialHR data with ease.'),
            rx.button(
                'Get Started',
                as_='a',
                href='/start-oauth',
                color_scheme='teal',
                size='2',
                mt='4',
                on_click=IndexState.get_credentials,
            ),
        ),
        height='100vh',
        bg='gray.50',
    )
