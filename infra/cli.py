"""infra-automator — CLI entry point.

Run ``infra --help`` for a list of subcommands. Configuration is read from
the project ``.env`` by default; override with ``--env-file``.
"""

from __future__ import annotations

import sys

import click

from . import __version__
from .commands.deploy import deploy_command
from .commands.destroy import destroy_command
from .commands.harden import harden_command
from .commands.status import status_command
from .commands.up import up_command
from .core.config import ConfigError, load_config
from .core.logger import console, setup_logging


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Opinionated CLI to provision, harden, deploy and destroy small footprints.",
)
@click.version_option(__version__, prog_name="infra")
@click.option(
    "--env-file",
    type=click.Path(dir_okay=False),
    default=None,
    help="Path to a .env file (defaults to ./.env).",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
@click.pass_context
def cli(ctx: click.Context, env_file: str | None, verbose: bool) -> None:
    setup_logging(verbose=verbose)
    try:
        ctx.obj = load_config(env_file)
    except ConfigError as exc:
        console.print(f"[bold red]configuration error:[/] {exc}")
        sys.exit(2)


cli.add_command(up_command)
cli.add_command(harden_command)
cli.add_command(deploy_command)
cli.add_command(status_command)
cli.add_command(destroy_command)


def main() -> None:
    """setuptools console-script entry point."""
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
