"""Main app file for the FactorialHR Analysis application."""

import reflex as rx

from factorialhr_analysis import pages, routes

# TODO: check if env variables in constants have been set

app = rx.App()
app.add_page(pages.index_page, route=routes.INDEX)
app.add_page(pages.working_time_verification_page, route=routes.VERIFICATION_ROUTE)
app.add_page(pages.authorize_oauth_page, route=routes.OAUTH_AUTHORIZE_ROUTE)
app.add_page(pages.start_oauth_process, route=routes.OAUTH_START_ROUTE)
