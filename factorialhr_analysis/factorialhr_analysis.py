"""Main app file for the FactorialHR Analysis application."""

import logging

import reflex as rx

from factorialhr_analysis import pages, routes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def backend_exception_handler(exc: Exception) -> None:
    """Handle backend exceptions."""
    logger = logging.getLogger(__name__)
    logger.exception('Backend exception', exc_info=exc)


def frontend_exception_handler(exc: Exception) -> None:
    """Handle frontend exceptions."""
    logger = logging.getLogger(__name__)
    logger.exception('Frontend exception', exc_info=exc)


app = rx.App()
# app.backend_exception_handler = backend_exception_handler  # noqa: ERA001
# app.frontend_exception_handler = frontend_exception_handler  # noqa: ERA001

app.add_page(pages.index_page, route=routes.INDEX)
app.add_page(pages.working_time_verification_page, route=routes.VERIFICATION_ROUTE)
app.add_page(pages.authorize_oauth_page, route=routes.OAUTH_AUTHORIZE_ROUTE)
app.add_page(pages.start_oauth_process, route=routes.OAUTH_START_ROUTE)
