import logging
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from ridiwise import __version__
from ridiwise.cmd import sync

app = typer.Typer(
    context_settings={'help_option_names': ['-h', '--help']},
    no_args_is_help=True,
)
app.add_typer(
    sync.app,
    name='sync',
    no_args_is_help=True,
)


def setup_logging(log_level: int = logging.WARNING):
    logging.basicConfig(
        level=log_level,
    )


def version_callback(value: bool):
    if value:
        print(f'{__version__}')
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    # pylint: disable=unused-argument
    version: Annotated[
        Optional[bool],
        typer.Option('--version', callback=version_callback, is_eager=True),
    ] = None,
    config_dir: Annotated[
        Optional[Path],
        typer.Option(envvar='RIDIWISE_CONFIG_DIR', help='Config home path'),
    ] = '~/.config/ridiwise',
    cache_dir: Annotated[
        Optional[Path],
        typer.Option(
            envvar='RIDIWISE_CACHE_DIR', help='Cache home path', writable=True
        ),
    ] = '~/.cache/ridiwise',
):
    """
    ridiwise: Sync Ridibooks book notes to Readwise.io
    """
    ctx.ensure_object(dict)
    ctx.obj = {
        'logger': logging.getLogger('ridiwise'),
        'config_dir': Path(config_dir).expanduser(),
        'cache_dir': Path(cache_dir).expanduser(),
    }


if __name__ == '__main__':
    app()
