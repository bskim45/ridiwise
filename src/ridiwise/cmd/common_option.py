import enum
from typing import Optional

import typer

from ridiwise.cmd.context import AuthState, ContextState


@enum.unique
class RidiAuthMethod(enum.StrEnum):
    # BROWSER_COOKIE = 'browser_cookie'
    HEADLESS_BROWSER = 'headless_browser'


def check_common_options(
    ctx: typer.Context,
    auth_method: RidiAuthMethod,
    user_id: Optional[str],
    password: Optional[str],
    headless_mode: bool,
    browser_timeout_seconds: int,
):
    context: ContextState = ctx.ensure_object(dict)

    auth_state: AuthState = {
        'auth_method': auth_method,
    }

    context['auth'] = auth_state
    context['headless_mode'] = headless_mode
    context['browser_timeout_seconds'] = browser_timeout_seconds

    if auth_method == RidiAuthMethod.HEADLESS_BROWSER:
        if not all([user_id, password]):
            raise typer.BadParameter('`user_id` and `password` must be provided.')

        auth_state['user_id'] = user_id
        auth_state['password'] = password


def common_params(
    ctx: typer.Context,
    auth_method: RidiAuthMethod = typer.Option(
        default=RidiAuthMethod.HEADLESS_BROWSER,
        envvar='RIDI_AUTH_METHOD',
        help='Authentication method to use with Ridibooks.',
    ),
    user_id: Optional[str] = typer.Option(
        default=None,
        envvar='RIDI_USER_ID',
        help='Ridibooks user ID.',
    ),
    password: Optional[str] = typer.Option(
        default=None,
        envvar='RIDI_PASSWORD',
        help='Ridibooks password.',
    ),
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
):
    ctx.ensure_object(dict)
    check_common_options(
        ctx=ctx,
        auth_method=auth_method,
        user_id=user_id,
        password=password,
        headless_mode=headless_mode,
        browser_timeout_seconds=browser_timeout_seconds,
    )
