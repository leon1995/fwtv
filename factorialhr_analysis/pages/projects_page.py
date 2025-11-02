"""Projects page for displaying project time calculations."""

import reflex as rx

from factorialhr_analysis import components, templates
from factorialhr_analysis.states.project_state import ProjectSettingsState, ProjectState


@rx.memo
def render_date_inputs() -> rx.Component:
    """Render the date input form."""
    return rx.hstack(
        rx.hstack(
            rx.text('Start date'),
            rx.input(
                type='date',
                name='start_date',
                value=ProjectSettingsState.start_date,
                on_change=ProjectSettingsState.set_start_date,
            ),
            align='center',
            spacing='1',
            min_width='max-content',
        ),
        rx.hstack(
            rx.text('End date'),
            rx.input(
                type='date',
                name='end_date',
                value=ProjectSettingsState.end_date,
                on_change=ProjectSettingsState.set_end_date,
            ),
            align='center',
            spacing='1',
            min_width='max-content',
        ),
        rx.checkbox(
            'Only active projects',
            default_checked=ProjectSettingsState.active,
            on_change=ProjectSettingsState.set_active,
        ),
        rx.cond(
            ProjectSettingsState.date_error,
            rx.tooltip(
                rx.button('Calculate', disabled=True),
                content='End date must be after start date.',
            ),
            rx.button(
                'Calculate',
                loading=ProjectState.is_loading_projects_times | ProjectState.is_loading_unrelated_minutes,
                on_click=ProjectState.calculate,
            ),
        ),
        spacing='3',
        align='center',
        width='100%',
    )


@rx.memo
def render_imputed_minutes_chart() -> rx.Component:
    """Render vertical bar chart for imputed minutes with different colors per project."""
    return rx.cond(
        ProjectState.project_times_data.length() > 0,
        rx.vstack(
            rx.heading('Project Time by Project', size='4'),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key='total',
                    name='Total Minutes',
                ),
                rx.recharts.x_axis(type_='number'),
                rx.recharts.y_axis(data_key='project', type_='category'),
                rx.recharts.graphing_tooltip(),
                rx.recharts.legend(),
                data=ProjectState.project_times_data,
                layout='vertical',
                width='100%',
                height=ProjectState.chart_height,
                margin={'top': 20, 'right': 20, 'left': 150, 'bottom': 20},
            ),
            width='100%',
            spacing='4',
        ),
        rx.text('No data available. Click Calculate to load project data.'),
    )


@rx.memo
def render_unrelated_minutes_chart() -> rx.Component:
    """Render bar chart for unrelated minutes."""
    return rx.cond(
        ProjectState.unrelated_minutes_data.length() > 0,
        rx.vstack(
            rx.heading('Unrelated Minutes by Employee', size='4'),
            rx.text(
                rx.cond(
                    ProjectState.total_unrelated_minutes > 0,
                    f'Total unrelated minutes: {ProjectState.total_unrelated_minutes}',
                    'Total unrelated minutes: 0',
                ),
                size='5',
                weight='bold',
            ),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key='minutes',
                    # fill='#82ca9d',
                    name='Unrelated Minutes',
                ),
                rx.recharts.x_axis(data_key='employee'),
                rx.recharts.y_axis(),
                rx.recharts.graphing_tooltip(),
                rx.recharts.legend(),
                data=ProjectState.unrelated_minutes_data,
                width='100%',
                height=400,
            ),
            width='100%',
            spacing='4',
        ),
        rx.text('No data available. Click Calculate to load unrelated minutes data.'),
    )


@components.requires_authentication
@templates.template
def projects_page() -> rx.Component:
    """Projects page showing project time calculations."""
    return rx.vstack(
        rx.heading('Project Time Analysis', size='6', weight='bold'),
        render_date_inputs(),
        rx.cond(
            ProjectState.error_message.is_not_none(),
            rx.callout.root(
                rx.callout.icon(),
                rx.callout.text(ProjectState.error_message),
                color_scheme='red',
            ),
            rx.fragment(),
        ),
        rx.vstack(
            render_imputed_minutes_chart(),
            render_unrelated_minutes_chart(),
            spacing='6',
            width='100%',
        ),
        width='100%',
        spacing='4',
    )
