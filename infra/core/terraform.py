"""Thin Python wrapper around the Terraform CLI.

We shell out rather than reimplementing state handling — Terraform is the
source of truth and a Python re-implementation would inevitably drift.
This module just gives the rest of the codebase a typed API surface.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import Config
from .logger import get_logger

log = get_logger()


class TerraformError(RuntimeError):
    """Raised when a terraform CLI invocation fails."""


def _ensure_terraform_installed() -> None:
    if shutil.which("terraform") is None:
        raise TerraformError(
            "`terraform` is not on PATH. Install from https://developer.hashicorp.com/terraform/install"
        )


def _env_for(cfg: Config) -> dict[str, str]:
    """Provider credentials are passed as TF_VAR_* — never written to disk."""
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"
    env["TF_INPUT"] = "0"
    env["TF_VAR_env"] = cfg.env
    env["TF_VAR_region"] = cfg.region
    env["TF_VAR_plan"] = cfg.plan
    env["TF_VAR_node_count"] = str(cfg.node_count)
    env["TF_VAR_ssh_public_key"] = cfg.ssh_public_key.expanduser().read_text().strip()
    if cfg.provider == "vultr":
        env["TF_VAR_vultr_api_key"] = cfg.vultr_api_key
    else:
        env["DIGITALOCEAN_TOKEN"] = cfg.digitalocean_token
        env["TF_VAR_do_token"] = cfg.digitalocean_token
    return env


def _run(args: list[str], cfg: Config, capture: bool = False) -> subprocess.CompletedProcess[str]:
    _ensure_terraform_installed()
    cwd = cfg.terraform_dir
    if not cwd.is_dir():
        raise TerraformError(f"Terraform directory does not exist: {cwd}")

    log.debug("Running: terraform %s (in %s)", " ".join(args), cwd)
    return subprocess.run(
        ["terraform", *args],
        cwd=cwd,
        env=_env_for(cfg),
        text=True,
        check=False,
        capture_output=capture,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init(cfg: Config) -> None:
    result = _run(["init", "-upgrade", "-no-color"], cfg)
    if result.returncode != 0:
        raise TerraformError("terraform init failed")


def apply(cfg: Config, auto_approve: bool = True) -> None:
    cmd = ["apply", "-no-color"]
    if auto_approve:
        cmd.append("-auto-approve")
    result = _run(cmd, cfg)
    if result.returncode != 0:
        raise TerraformError("terraform apply failed")


def destroy(cfg: Config, auto_approve: bool = True) -> None:
    cmd = ["destroy", "-no-color"]
    if auto_approve:
        cmd.append("-auto-approve")
    result = _run(cmd, cfg)
    if result.returncode != 0:
        raise TerraformError("terraform destroy failed")


def outputs(cfg: Config) -> dict[str, Any]:
    """Return parsed terraform outputs, or an empty dict if no state exists."""
    result = _run(["output", "-json"], cfg, capture=True)
    if result.returncode != 0:
        # No state yet — treat as "nothing provisioned".
        if "No outputs found" in (result.stderr or "") or "state file" in (result.stderr or ""):
            return {}
        raise TerraformError(f"terraform output failed: {result.stderr}")
    try:
        raw = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise TerraformError(f"could not parse terraform output JSON: {exc}") from exc
    return {k: v.get("value") for k, v in raw.items()}


def server_ips(cfg: Config) -> list[str]:
    """Convenience accessor for the ``server_ips`` output expected from every stack."""
    out = outputs(cfg)
    ips = out.get("server_ips") or []
    if isinstance(ips, str):
        return [ips]
    return list(ips)


def state_exists(cfg: Config) -> bool:
    state = cfg.terraform_dir / "terraform.tfstate"
    return state.is_file() and state.stat().st_size > 0


def write_inventory(cfg: Config, ips: list[str], path: Path) -> Path:
    """Write an Ansible-compatible inventory YAML based on terraform output."""
    content = [
        "all:",
        "  hosts:",
    ]
    for i, ip in enumerate(ips, start=1):
        content.append(f"    node-{i:02d}:")
        content.append(f"      ansible_host: {ip}")
    content.append("  vars:")
    content.append("    ansible_user: root")
    content.append(f"    ansible_ssh_private_key_file: {cfg.ssh_private_key}")
    content.append(f"    admin_user: {cfg.admin_user}")
    content.append(f"    ssh_port: {cfg.ssh_port}")
    content.append(
        "    extra_open_ports: [" + ", ".join(str(p) for p in cfg.extra_open_ports) + "]"
    )
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
