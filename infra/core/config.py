"""Configuration loader.

Reads the project ``.env`` (or whatever ``--env-file`` points at) into a
typed dataclass.  Centralising config here keeps the rest of the codebase
free of ``os.environ`` lookups, which makes the CLI trivial to test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROVIDERS = ("vultr", "digitalocean")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    provider: str
    env: str
    region: str
    plan: str
    node_count: int

    vultr_api_key: str
    digitalocean_token: str

    ssh_public_key: Path
    ssh_private_key: Path
    admin_user: str
    ssh_port: int
    extra_open_ports: list[int] = field(default_factory=list)

    compose_project: str = "infra-app"
    app_image_tag: str = "latest"

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    @property
    def terraform_dir(self) -> Path:
        return Path("terraform") / self.provider

    @property
    def provider_credential(self) -> str:
        return self.vultr_api_key if self.provider == "vultr" else self.digitalocean_token

    def validate_for_provisioning(self) -> None:
        if not self.provider_credential:
            env_var = "VULTR_API_KEY" if self.provider == "vultr" else "DIGITALOCEAN_TOKEN"
            raise ConfigError(f"{env_var} is not set — required for provider '{self.provider}'.")
        if not self.ssh_public_key.expanduser().is_file():
            raise ConfigError(f"SSH public key not found at {self.ssh_public_key}")


def _parse_port_list(raw: str) -> list[int]:
    return [int(p.strip()) for p in raw.split(",") if p.strip()]


def load_config(env_file: str | os.PathLike[str] | None = None) -> Config:
    """Load configuration from ``.env`` (or override) + process environment."""
    if env_file:
        load_dotenv(env_file, override=False)
    else:
        load_dotenv(override=False)

    provider = os.getenv("INFRA_PROVIDER", "vultr").lower()
    if provider not in PROVIDERS:
        raise ConfigError(
            f"Unsupported INFRA_PROVIDER '{provider}'. Choose one of: {', '.join(PROVIDERS)}"
        )

    try:
        node_count = int(os.getenv("INFRA_NODE_COUNT", "1"))
        ssh_port = int(os.getenv("SSH_PORT", "22"))
    except ValueError as exc:
        raise ConfigError(f"Numeric config could not be parsed: {exc}") from exc

    return Config(
        provider=provider,
        env=os.getenv("INFRA_ENV", "dev"),
        region=os.getenv("INFRA_REGION", "ewr"),
        plan=os.getenv("INFRA_PLAN", "vc2-1c-1gb"),
        node_count=node_count,
        vultr_api_key=os.getenv("VULTR_API_KEY", ""),
        digitalocean_token=os.getenv("DIGITALOCEAN_TOKEN", ""),
        ssh_public_key=Path(os.getenv("SSH_PUBLIC_KEY", "~/.ssh/id_ed25519.pub")).expanduser(),
        ssh_private_key=Path(os.getenv("SSH_PRIVATE_KEY", "~/.ssh/id_ed25519")).expanduser(),
        admin_user=os.getenv("ADMIN_USER", "deploy"),
        ssh_port=ssh_port,
        extra_open_ports=_parse_port_list(os.getenv("EXTRA_OPEN_PORTS", "")),
        compose_project=os.getenv("COMPOSE_PROJECT", "infra-app"),
        app_image_tag=os.getenv("APP_IMAGE_TAG", "latest"),
    )
