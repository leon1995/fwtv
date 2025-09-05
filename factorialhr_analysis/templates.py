"""Templates for the web application."""

import functools

import reflex as rx

from factorialhr_analysis import components


def template(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Wrap a page in the main template."""

    @functools.wraps(page)
    def page_template() -> rx.Component:
        return rx.fragment(
            components.navbar(),
            rx.box(
                page(),
                padding_top='1em',  # Space between navbar and content
                padding_left='1em',
                padding_right='1em',
            ),
        )

    return page_template
