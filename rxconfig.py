"""Reflex configuration file."""

import reflex as rx

config = rx.Config(
    app_name='factorialhr_analysis',
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    telemetry_enabled=False,
    env_file='.env',
    show_built_with_reflex=False,
)
