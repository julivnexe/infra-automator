"""`infra destroy` — tear everything down cleanly."""

from __future__ import annotations

from pathlib import Path

import click

from ..core import terraform
from ..core.config import Config
from ..core.logger import get_logger

log = get_logger()


@click.command("destroy")
@click.option("--yes", is_flag=True, help="Skip the destructive-action confirmation.")
@click.pass_obj
def destroy_command(cfg: Config, yes: bool) -> None:
    """Run `terraform destroy` and clean up local state artefacts."""
    if not terraform.state_exists(cfg):
        log.info("no terraform state for provider '%s' — nothing to destroy", cfg.provider)
        return

    ips = terraform.server_ips(cfg)
    log.warning(
        "this will permanently destroy %d node(s) on %s: %s",
        len(ips),
        cfg.provider,
        ", ".join(ips) or "(none reported)",
    )

    if not yes and not click.confirm("Proceed with destruction?", default=False):
        log.info("aborted by user")
        return

    log.info("[cyan]→[/] terraform destroy")
    terraform.destroy(cfg, auto_approve=True)

    inventory = Path(".infra/inventory.yml")
    if inventory.is_file():
        inventory.unlink()
        log.info("removed %s", inventory)

    log.info("[green]✓[/] destroy complete")
