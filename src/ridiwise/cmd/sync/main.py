import typer

from ridiwise.cmd.sync import longblack, ridibooks

app = typer.Typer()


@app.callback()
def main():
    """
    Sync book/article highlights to another service.
    """


app.add_typer(
    ridibooks.app,
    no_args_is_help=True,
)

app.add_typer(
    longblack.app,
    no_args_is_help=True,
)
