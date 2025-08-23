"""Reflex configuration file."""

import reflex as rx

config = rx.Config(
    app_name='factorialhr_analysis',
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
