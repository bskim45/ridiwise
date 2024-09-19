from collections import defaultdict

import typer

from ridiwise.cmd.context import ContextState


def check_common_options(
    ctx: typer.Context,
    headless_mode: bool,
    browser_timeout_seconds: int,
    error_on_empty_source: bool,
):
    context: ContextState = ctx.ensure_object(dict)

    if 'auths' not in context:
        context['auths'] = defaultdict()

    context['headless_mode'] = headless_mode
    context['browser_timeout_seconds'] = browser_timeout_seconds
    context['error_on_empty_source'] = error_on_empty_source


def common_params(
    ctx: typer.Context,
    headless_mode: bool = typer.Option(
        True,
        envvar='HEADLESS_MODE',
        help='Hide the browser window (headless mode).',
    ),
    browser_timeout_seconds: int = typer.Option(
        default=10,
        envvar='BROWSER_TIMEOUT_SECONDS',
        help='Timeout for browser page loading in seconds.',
    ),
    error_on_empty_source: bool = typer.Option(
        default=False,
        envvar='ERROR_ON_EMPTY_SOURCE',
        help='Exit with exit code 2 if no article/book is found from the source.',
    ),
):
    ctx.ensure_object(dict)
    check_common_options(
        ctx=ctx,
        headless_mode=headless_mode,
        browser_timeout_seconds=browser_timeout_seconds,
        error_on_empty_source=error_on_empty_source,
    )
