import subprocess
from typing import TYPE_CHECKING

import click

import prompt_checking
from prompt_checking.config import configured_scheduler

if TYPE_CHECKING:
    from resonate.promise import Promise


@click.group(
    context_settings={
        "help_option_names": [
            "-h",
            "--help",
        ],
        "show_default": True,
    },
)
@click.version_option(None, "-v", "--version")
def cli() -> None:
    """
    Resonate Python SDK - AI Demo Application.

    AI application need durable executions <3.
    """


@cli.command()
@click.argument("query")
def search(query: str) -> None:
    s = configured_scheduler()
    p: Promise[str] = s.run("search", prompt_checking.use_case, query=query)
    click.echo(p.result())


@cli.command()
def up() -> None:
    subprocess.run(
        args=["uvicorn", "prompt_checking.api:app", "--port", "8000"], check=False
    )
