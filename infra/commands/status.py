"""`infra status` — show health of the current infrastructure."""

from __future__ import annotations

import click
from rich.table import Table

from ..core import terraform
from ..core.config import Config
from ..core.logger import console, get_logger
from ..core.ssh import SshTarget, run, wait_for_port

log = get_logger()


@click.command("status")
@click.pass_obj
def status_command(cfg: Config) -> None:
    """Print a snapshot of provisioned servers and running containers."""
    if not terraform.state_exists(cfg):
        log.warning("no terraform state for provider '%s' — nothing provisioned yet", cfg.provider)
        return

    ips = terraform.server_ips(cfg)
    if not ips:
        log.info("state exists but no server_ips output — was apply successful?")
        return

    table = Table(title=f"infra-automator — {cfg.provider}/{cfg.env}", border_style="cyan")
    table.add_column("Host", style="bold")
    table.add_column("SSH", justify="center")
    table.add_column("Uptime", overflow="fold")
    table.add_column("Containers", justify="right")
    table.add_column("Disk", justify="right")

    for ip in ips:
        reachable = wait_for_port(ip, cfg.ssh_port, timeout=5)
        if not reachable:
            table.add_row(ip, "[red]✗[/]", "-", "-", "-")
            continue

        target = SshTarget(host=ip, user=cfg.admin_user, key_path=cfg.ssh_private_key, port=cfg.ssh_port)
        try:
            _, uptime, _ = run(target, "uptime -p", check=False)
            _, containers, _ = run(
                target, "sudo docker ps --format '{{.Names}}' 2>/dev/null | wc -l", check=False
            )
            _, disk, _ = run(target, "df -h / | awk 'NR==2 {print $5}'", check=False)
        except Exception as exc:
            log.debug("status probe failed for %s: %s", ip, exc)
            table.add_row(ip, "[yellow]?[/]", "ssh ok, probe failed", "-", "-")
            continue

        table.add_row(
            ip,
            "[green]✓[/]",
            uptime.strip() or "unknown",
            containers.strip() or "0",
            disk.strip() or "?",
        )

    console.print(table)
