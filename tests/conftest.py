"""Shared pytest fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def fake_ssh_key(tmp_path: Path) -> Path:
    pub = tmp_path / "id_test.pub"
    pub.write_text("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAItest test@host\n")
    return pub


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip INFRA_* / VULTR_* / DIGITALOCEAN_* from the env per test."""
    for key in list(os.environ):
        if key.startswith(
            ("INFRA_", "VULTR_", "DIGITALOCEAN_", "SSH_", "ADMIN_", "EXTRA_", "COMPOSE_", "APP_")
        ):
            monkeypatch.delenv(key, raising=False)
