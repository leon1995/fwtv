import factorialhr
import reflex as rx

from factorialhr_analysis import constants, states, templates


class IndexState(rx.State):
    """State for the index page."""

    is_loading: rx.Field[bool] = rx.field(default=False)

    @rx.event
    async def get_credentials(self):
        self.is_loading = True
        yield
        oauth_state = await self.get_state(states.OAuthSessionState)
        try:
            async with factorialhr.ApiClient(
                base_url=constants.ENVIRONMENT_URL, auth=oauth_state.get_auth()
            ) as api_client:
                shifts = await factorialhr.ShiftsEndpoint(api_client).all(timeout=100)
        finally:
            self.is_loading = False


@templates.template
def index_page() -> rx.Component:
    """The index page of the application."""
    return rx.vstack(
        rx.heading('Welcome to FactorialHR Analysis', size='4'),
        rx.hstack(
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
            border_radius='1em',
            border='1px solid',
            padding='0.5em',
        ),
        rx.text('loaded shifts:', states.DataState.len_of_shifts),
        bg=rx.color('accent'),
        align='center',
    )
