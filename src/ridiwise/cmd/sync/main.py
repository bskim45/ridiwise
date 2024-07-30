import typer
from typing_extensions import Annotated

from ridiwise.api.readwise import ReadwiseClient
from ridiwise.api.ridibooks import RidiClient
from ridiwise.cmd.common_option import common_params
from ridiwise.cmd.context import AuthState
from ridiwise.cmd.utils import with_extra_parameters

app = typer.Typer()


@app.callback()
def main():
    """
    Sync Ridibooks book notes to another service.
    """


@app.command()
@with_extra_parameters(common_params)
def readwise(
    ctx: typer.Context,
    readwise_token: Annotated[
        str,
        typer.Option(
            envvar='READWISE_TOKEN',
            help='Readwise.io API token. https://readwise.io/access_token',
        ),
    ],
):
    """
    Sync Ridibooks book notes to Readwise.io.
    """

    logger = ctx.obj['logger']
    auth_state: AuthState = ctx.obj['auth']

    with (
        RidiClient(
            user_id=auth_state['user_id'],
            password=auth_state['password'],
            cache_dir=ctx.obj['cache_dir'],
            headless=ctx.obj['headless_mode'],
        ) as ridi_client,
        ReadwiseClient(token=readwise_token) as readwise_client,
    ):
        books = ridi_client.get_books_from_shelf()

        result_count = {
            'books': 0,
            'highlights': 0,
        }

        for book in books:
            readwise_client.create_highlights(
                highlights=[
                    {
                        'text': note['highlighted_text'],
                        'title': book['book_title'],
                        'source_type': 'ridibooks',
                        'category': 'books',
                        'author': ', '.join(book['authors']),
                        'highlighted_at': note['created_date'].isoformat(),
                        'note': note['memo'],
                        'source_url': book['book_url'],
                        'highlight_url': f'{book["book_notes_url"]}#annotation_{note["id"]}',  # noqa: E501 pylint: disable=line-too-long
                        'image_url': book['book_cover_image_url'],
                    }
                    for note in book['notes']
                ]
            )

            result_count['books'] += 1
            result_count['highlights'] += len(book['notes'])

            logger.info(
                'Created Readwise highlights: '
                f"`{book['book_title']}` / {len(book['notes'])}"
            )

        print('Synced notes to Readwise.io:')
        print('Books: ', result_count['books'])
        print('Highlights: ', result_count['highlights'])
