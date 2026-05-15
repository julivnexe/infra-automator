"""Tests for infra.core.config."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from infra.core.config import Config, ConfigError, load_config


def test_defaults_to_vultr(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = load_config(env_file=tmp_path / "missing.env")
    assert cfg.provider == "vultr"
    assert cfg.env == "dev"
    assert cfg.node_count == 1


def test_explicit_env_overrides_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("INFRA_PROVIDER", "digitalocean")
    monkeypatch.setenv("INFRA_REGION", "fra1")
    monkeypatch.setenv("INFRA_NODE_COUNT", "3")
    monkeypatch.setenv("EXTRA_OPEN_PORTS", "8080, 9090,3000")

    cfg = load_config(env_file=tmp_path / "missing.env")
    assert cfg.provider == "digitalocean"
    assert cfg.region == "fra1"
    assert cfg.node_count == 3
    assert cfg.extra_open_ports == [8080, 9090, 3000]


def test_invalid_provider_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("INFRA_PROVIDER", "aws")
    with pytest.raises(ConfigError, match="Unsupported INFRA_PROVIDER"):
        load_config(env_file=tmp_path / "missing.env")


def test_invalid_node_count_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("INFRA_NODE_COUNT", "not-a-number")
    with pytest.raises(ConfigError, match="Numeric config"):
        load_config(env_file=tmp_path / "missing.env")


def test_validate_for_provisioning_requires_credentials(
    monkeypatch: pytest.MonkeyPatch, fake_ssh_key: Path, tmp_path: Path
) -> None:
    monkeypatch.setenv("SSH_PUBLIC_KEY", str(fake_ssh_key))
    cfg = load_config(env_file=tmp_path / "missing.env")
    with pytest.raises(ConfigError, match="VULTR_API_KEY"):
        cfg.validate_for_provisioning()


def test_validate_for_provisioning_happy_path(
    monkeypatch: pytest.MonkeyPatch, fake_ssh_key: Path, tmp_path: Path
) -> None:
    monkeypatch.setenv("VULTR_API_KEY", "vlt_test")
    monkeypatch.setenv("SSH_PUBLIC_KEY", str(fake_ssh_key))
    cfg = load_config(env_file=tmp_path / "missing.env")
    cfg.validate_for_provisioning()  # must not raise


def test_terraform_dir_matches_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("INFRA_PROVIDER", "digitalocean")
    cfg = load_config(env_file=tmp_path / "missing.env")
    assert cfg.terraform_dir.as_posix() == "terraform/digitalocean"


def test_config_is_frozen() -> None:
    cfg = Config(
        provider="vultr",
        env="dev",
        region="ewr",
        plan="vc2-1c-1gb",
        node_count=1,
        vultr_api_key="",
        digitalocean_token="",
        ssh_public_key=Path("/tmp/x.pub"),
        ssh_private_key=Path("/tmp/x"),
        admin_user="deploy",
        ssh_port=22,
    )
    with pytest.raises(FrozenInstanceError):
        cfg.env = "prod"  # type: ignore[misc]
