"""`infra harden` — apply baseline security hardening.

Strategy:
- If ``ansible-playbook`` is installed, run ``ansible/harden.yml`` against
  the inventory written by ``infra up``.
- Otherwise, fall back to ``scripts/harden.sh`` executed over SSH per host.

Both paths converge on the same end-state: non-root admin user with SSH
keys, password+root SSH disabled, UFW deny-by-default, fail2ban watching
sshd, automatic security upgrades enabled.
"""

from __future__ import annotations

from pathlib import Path

import click

from ..core import terraform
from ..core.config import Config
from ..core.logger import get_logger
from ..core.ssh import SshTarget, run, upload
from ..utils.helpers import run_local, which

log = get_logger()


@click.command("harden")
@click.option("--force-shell", is_flag=True, help="Skip Ansible and use the shell fallback.")
@click.pass_obj
def harden_command(cfg: Config, force_shell: bool) -> None:
    """Harden every node tracked in the current Terraform state."""
    ips = terraform.server_ips(cfg)
    if not ips:
        log.error("no servers found — run `infra up` first")
        raise SystemExit(1)

    if not force_shell and which("ansible-playbook"):
        _run_ansible(cfg)
    else:
        if force_shell:
            log.info("--force-shell set; using shell fallback")
        else:
            log.info("ansible-playbook not found on PATH; using shell fallback")
        _run_shell_fallback(cfg, ips)


def _run_ansible(cfg: Config) -> None:
    inventory = Path(".infra/inventory.yml")
    if not inventory.is_file():
        log.error("inventory missing at %s — re-run `infra up`", inventory)
        raise SystemExit(1)

    log.info("[cyan]→[/] running ansible playbook (ansible/harden.yml)")
    rc = run_local(
        [
            "ansible-playbook",
            "-i",
            str(inventory),
            "ansible/harden.yml",
            "--extra-vars",
            f"admin_user={cfg.admin_user} ssh_port={cfg.ssh_port}",
        ]
    )
    if rc != 0:
        log.error("ansible-playbook exited with code %d", rc)
        raise SystemExit(rc)
    log.info("[green]✓[/] hardening complete")


def _run_shell_fallback(cfg: Config, ips: list[str]) -> None:
    script = Path("scripts/harden.sh")
    if not script.is_file():
        log.error("hardening script missing at %s", script)
        raise SystemExit(1)

    pubkey = cfg.ssh_public_key.expanduser().read_text().strip()

    for ip in ips:
        log.info("[cyan]→[/] hardening %s", ip)
        target = SshTarget(host=ip, user="root", key_path=cfg.ssh_private_key, port=22)
        upload(target, script, "/root/harden.sh")
        run(target, "chmod +x /root/harden.sh")
        cmd = (
            f"ADMIN_USER={cfg.admin_user} "
            f"SSH_PORT={cfg.ssh_port} "
            f'ADMIN_PUBKEY="{pubkey}" '
            f'EXTRA_OPEN_PORTS="{",".join(str(p) for p in cfg.extra_open_ports)}" '
            "bash /root/harden.sh"
        )
        rc, _, _ = run(target, cmd, check=False)
        if rc != 0:
            log.error("hardening failed on %s (rc=%d)", ip, rc)
            raise SystemExit(rc)
        log.info("[green]✓[/] %s hardened", ip)
