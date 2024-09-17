import itertools
from typing import Optional

import typer
from typing_extensions import Annotated

from ridiwise.api.longblack import LongblackClient
from ridiwise.api.readwise import ReadwiseClient
from ridiwise.cmd.common_option import common_params
from ridiwise.cmd.context import AuthMethod, AuthState, ContextState
from ridiwise.cmd.utils import with_extra_parameters

PROVIDER = 'longblack'

app = typer.Typer(name='longblack')


@app.callback()
def main():
    """
    Sync Longblack scraps(highlights) to another service.
    """


def check_longblack_common_options(
    ctx: typer.Context,
    auth_method: AuthMethod,
    user_id: Optional[str],
    password: Optional[str],
):
    context: ContextState = ctx.ensure_object(dict)

    auth_state: AuthState = {
        'auth_method': auth_method,
    }

    if auth_method == AuthMethod.HEADLESS_BROWSER:
        if not all([user_id, password]):
            raise typer.BadParameter('`user_id` and `password` must be provided.')

        auth_state['user_id'] = user_id
        auth_state['password'] = password

    context['auths'][PROVIDER] = auth_state


def longblack_common_params(
    ctx: typer.Context,
    auth_method: AuthMethod = typer.Option(
        default=AuthMethod.HEADLESS_BROWSER,
        envvar='LONGBLACK_AUTH_METHOD',
        help='Authentication method to use with Longblack.',
    ),
    user_id: Optional[str] = typer.Option(
        default=None,
        envvar='LONGBLACK_USER_ID',
        help='Longblack user ID.',
    ),
    password: Optional[str] = typer.Option(
        default=None,
        envvar='LONGBLACK_PASSWORD',
        help='Longblack password.',
    ),
):
    ctx.ensure_object(dict)
    check_longblack_common_options(
        ctx=ctx,
        auth_method=auth_method,
        user_id=user_id,
        password=password,
    )


@app.command()
@with_extra_parameters(common_params)
@with_extra_parameters(longblack_common_params)
def readwise(
    ctx: typer.Context,
    readwise_token: Annotated[
        str,
        typer.Option(
            envvar='READWISE_TOKEN',
            help='Readwise.io API token. https://readwise.io/access_token',
        ),
    ],
    tags: Annotated[
        Optional[list[str]],
        typer.Option(
            help='Tags to attach to the highlights. Multiple tags can be provided.',
        ),
    ] = None,
):
    """
    Sync Longblack scraps to Readwise.io.
    """

    context: ContextState = ctx.ensure_object(dict)

    with (
        LongblackClient(
            user_id=context['auths'][PROVIDER]['user_id'],
            password=context['auths'][PROVIDER]['password'],
            cache_dir=context['cache_dir'],
            headless=context['headless_mode'],
            browser_timeout_seconds=context['browser_timeout_seconds'],
        ) as longblack_client,
        ReadwiseClient(token=readwise_token) as readwise_client,
    ):
        scraps = longblack_client.get_scraps()

        if not scraps:
            raise typer.Abort('No scraps found.')

        result_count = {
            'articles': 0,
            'highlights': 0,
        }

        highlights_response = readwise_client.create_highlights(
            highlights=[
                {
                    'text': scrap['highlighted_text'],
                    'title': scrap['note']['title'],
                    'source_type': PROVIDER,
                    'category': 'articles',
                    'author': scrap['note']['author'],
                    'highlighted_at': scrap['created_datetime'].isoformat(),
                    'note': scrap['memo'],
                    'source_url': scrap['note']['note_url'],
                    'highlight_url': scrap['scrap_url'],
                    'image_url': scrap['note']['cover_image_url'],
                }
                for scrap in scraps
            ]
        )

        modified_highlight_ids = itertools.chain.from_iterable(
            article_result['modified_highlights']
            for article_result in highlights_response
        )

        if tags:
            for highlight_id, tag in zip(modified_highlight_ids, tags):
                readwise_client.create_highlight_tag(
                    highlight_id=highlight_id,
                    tag=tag,
                )

        result_count['articles'] = len({scrap['note']['note_id'] for scrap in scraps})
        result_count['highlights'] = len(scraps)

        print('Synced notes to Readwise.io:')
        print('Articles: ', result_count['articles'])
        print('Highlights: ', result_count['highlights'])
