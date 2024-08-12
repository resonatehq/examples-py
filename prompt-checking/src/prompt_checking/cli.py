import click
import resonate

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
    s = resonate.testing.dst(seeds=[1])[0]
    s.add(prompt_checking.use_case, query=query)
    result = s.run()[0].result()
    click.echo(result)
