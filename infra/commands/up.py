"""`infra up` — provision cloud infrastructure with Terraform."""

from __future__ import annotations

from pathlib import Path

import click
from rich.panel import Panel

from ..core import terraform
from ..core.config import Config
from ..core.logger import console, get_logger
from ..core.ssh import wait_for_port

log = get_logger()


@click.command("up")
@click.option("--yes", is_flag=True, help="Skip the interactive confirmation prompt.")
@click.option("--skip-wait", is_flag=True, help="Don't wait for SSH to come up after apply.")
@click.pass_obj
def up_command(cfg: Config, yes: bool, skip_wait: bool) -> None:
    """Provision servers via Terraform for the configured provider."""
    cfg.validate_for_provisioning()

    console.print(
        Panel.fit(
            f"[bold]Provider[/]   {cfg.provider}\n"
            f"[bold]Env[/]        {cfg.env}\n"
            f"[bold]Region[/]     {cfg.region}\n"
            f"[bold]Plan[/]       {cfg.plan}\n"
            f"[bold]Nodes[/]      {cfg.node_count}",
            title="infra up",
            border_style="cyan",
        )
    )

    if not yes and not click.confirm("Apply this plan?", default=True):
        log.info("aborted by user")
        return

    log.info("[cyan]→[/] terraform init")
    terraform.init(cfg)

    log.info("[cyan]→[/] terraform apply")
    terraform.apply(cfg, auto_approve=True)

    ips = terraform.server_ips(cfg)
    if not ips:
        log.warning("terraform apply succeeded but no `server_ips` output was found")
        return

    log.info("[green]✓[/] provisioned %d node(s): %s", len(ips), ", ".join(ips))

    # Persist an Ansible inventory so `infra harden` can run unattended.
    state_dir = Path(".infra")
    state_dir.mkdir(exist_ok=True)
    inventory = terraform.write_inventory(cfg, ips, state_dir / "inventory.yml")
    log.info("[green]✓[/] wrote inventory → %s", inventory)

    if not skip_wait:
        for ip in ips:
            log.info("waiting for SSH on %s:22 …", ip)
            if wait_for_port(ip, 22, timeout=240):
                log.info("[green]✓[/] %s reachable", ip)
            else:
                log.warning("%s did not open port 22 within timeout", ip)

    console.print(
        Panel.fit(
            "Next steps:\n"
            "  [cyan]infra harden[/]   — apply baseline hardening\n"
            "  [cyan]infra deploy[/]   — push the compose stack",
            border_style="green",
        )
    )
