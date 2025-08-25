"""Main app file for the FactorialHR Analysis application."""

import dotenv
import reflex as rx

from factorialhr_analysis import pages, routes

dotenv.load_dotenv()


app = rx.App()
app.add_page(pages.index_page, route=routes.INDEX)
app.add_page(pages.login_page, route=routes.LOGIN_ROUTE)
