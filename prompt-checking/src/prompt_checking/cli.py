import subprocess

import click
from duckduckgo_search import DDGS
from resonate.scheduler import Scheduler

import prompt_checking


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
    s = Scheduler()
    s._deps.set("model", "llama3.1")
    s._deps.set("duckduckgo_client", DDGS())
    p = s.run("search", prompt_checking.use_case, query=query)
    click.echo(p.result())


@cli.command()
def up() -> None:
    subprocess.run(
        args=["uvicorn", "prompt_checking.api:app", "--port", "8000"], check=False
    )
