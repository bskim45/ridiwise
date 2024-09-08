from typing import Optional

import typer
from typing_extensions import Annotated

from ridiwise.api.readwise import ReadwiseClient
from ridiwise.api.ridibooks import RidiClient
from ridiwise.cmd.common_option import common_params
from ridiwise.cmd.context import ContextState
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
    tags: Annotated[
        Optional[list[str]],
        typer.Option(
            help='Tags to attach to the highlights. Multiple tags can be provided.',
        ),
    ] = None,
):
    """
    Sync Ridibooks book notes to Readwise.io.
    """

    context: ContextState = ctx.ensure_object(dict)
    logger = context['logger']

    with (
        RidiClient(
            user_id=context['auth']['user_id'],
            password=context['auth']['password'],
            cache_dir=context['cache_dir'],
            headless=context['headless_mode'],
            browser_timeout_seconds=context['browser_timeout_seconds'],
        ) as ridi_client,
        ReadwiseClient(token=readwise_token) as readwise_client,
    ):
        books = ridi_client.get_books_from_shelf()

        result_count = {
            'books': 0,
            'highlights': 0,
        }

        for book in books:
            highlights_response = readwise_client.create_highlights(
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
                        'highlight_url': (
                            f'{book["book_notes_url"]}#annotation_{note["id"]}'
                        ),
                        'image_url': book['book_cover_image_url'],
                    }
                    for note in book['notes']
                ]
            )

            modified_highlight_ids = highlights_response[0]['modified_highlights']

            if tags:
                for highlight_id, tag in zip(modified_highlight_ids, tags):
                    readwise_client.create_highlight_tag(
                        highlight_id=highlight_id,
                        tag=tag,
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
