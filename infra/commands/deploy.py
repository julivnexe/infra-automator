"""`infra deploy` — push the Docker Compose stack to each server."""

from __future__ import annotations

from pathlib import Path

import click

from ..core import terraform
from ..core.config import Config
from ..core.logger import get_logger
from ..core.ssh import SshTarget, run, upload_tree

log = get_logger()

REMOTE_DIR = "/opt/infra-app"


@click.command("deploy")
@click.option(
    "--stack",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("deploy"),
    show_default=True,
    help="Local directory containing docker-compose.yml and supporting files.",
)
@click.option(
    "--pull/--no-pull", default=True, show_default=True, help="docker compose pull before up."
)
@click.pass_obj
def deploy_command(cfg: Config, stack: Path, pull: bool) -> None:
    """Sync the compose stack to each server and bring it up."""
    ips = terraform.server_ips(cfg)
    if not ips:
        log.error("no servers found — run `infra up` first")
        raise SystemExit(1)

    compose_file = stack / "docker-compose.yml"
    if not compose_file.is_file():
        log.error("docker-compose.yml not found in %s", stack)
        raise SystemExit(1)

    for ip in ips:
        log.info("[cyan]→[/] deploying to %s", ip)
        target = SshTarget(
            host=ip, user=cfg.admin_user, key_path=cfg.ssh_private_key, port=cfg.ssh_port
        )

        # Ensure Docker is present — harden role installs it, but be defensive.
        rc, _, _ = run(target, "command -v docker", check=False)
        if rc != 0:
            log.error("docker not installed on %s — run `infra harden` first", ip)
            raise SystemExit(1)

        run(target, f"sudo mkdir -p {REMOTE_DIR} && sudo chown {cfg.admin_user}: {REMOTE_DIR}")
        upload_tree(target, stack, REMOTE_DIR)

        env_line = (
            f"COMPOSE_PROJECT_NAME={cfg.compose_project} " f"APP_IMAGE_TAG={cfg.app_image_tag}"
        )

        if pull:
            run(target, f"cd {REMOTE_DIR} && {env_line} sudo -E docker compose pull")
        run(target, f"cd {REMOTE_DIR} && {env_line} sudo -E docker compose up -d --remove-orphans")

        rc, out, _ = run(target, f"cd {REMOTE_DIR} && sudo docker compose ps", check=False)
        log.info("\n%s", out.strip() or "(no output)")
        log.info("[green]✓[/] %s deployed", ip)
