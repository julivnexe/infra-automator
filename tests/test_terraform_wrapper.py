"""Tests for the infra.core.terraform wrapper — pure unit, no shell-out."""

from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from infra.core import terraform as tf
from infra.core.config import Config


def _cfg(tmp_path: Path) -> Config:
    pub = tmp_path / "id.pub"
    pub.write_text("ssh-ed25519 AAA test\n")
    (tmp_path / "terraform" / "vultr").mkdir(parents=True)
    return Config(
        provider="vultr",
        env="test",
        region="ewr",
        plan="vc2-1c-1gb",
        node_count=2,
        vultr_api_key="vlt_test",
        digitalocean_token="",
        ssh_public_key=pub,
        ssh_private_key=pub.with_suffix(""),
        admin_user="deploy",
        ssh_port=22,
        extra_open_ports=[9090],
    )


def test_outputs_returns_empty_when_no_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg(tmp_path)

    def fake_run(args, cfg, capture=False):  # type: ignore[no-untyped-def]
        return CompletedProcess(args=args, returncode=1, stdout="", stderr="No outputs found")

    monkeypatch.setattr(tf, "_ensure_terraform_installed", lambda: None)
    monkeypatch.setattr(tf, "_run", fake_run)

    assert tf.outputs(cfg) == {}
    assert tf.server_ips(cfg) == []


def test_outputs_parses_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg(tmp_path)

    payload = json.dumps(
        {
            "server_ips": {"value": ["1.2.3.4", "5.6.7.8"], "type": "list"},
            "hostnames": {"value": ["a", "b"], "type": "list"},
        }
    )

    def fake_run(args, cfg, capture=False):  # type: ignore[no-untyped-def]
        return CompletedProcess(args=args, returncode=0, stdout=payload, stderr="")

    monkeypatch.setattr(tf, "_ensure_terraform_installed", lambda: None)
    monkeypatch.setattr(tf, "_run", fake_run)

    assert tf.server_ips(cfg) == ["1.2.3.4", "5.6.7.8"]


def test_write_inventory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    out = tmp_path / "inv.yml"
    tf.write_inventory(cfg, ["10.0.0.1", "10.0.0.2"], out)

    text = out.read_text()
    assert "node-01" in text
    assert "node-02" in text
    assert "ansible_host: 10.0.0.1" in text
    assert "ansible_host: 10.0.0.2" in text
    assert f"admin_user: {cfg.admin_user}" in text
