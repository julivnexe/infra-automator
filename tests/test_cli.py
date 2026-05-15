"""CLI surface tests — exercise Click wiring without hitting the cloud."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from infra import __version__
from infra.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_top_level_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for cmd in ("up", "harden", "deploy", "status", "destroy"):
        assert cmd in result.output


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_invalid_provider_exits_cleanly(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("INFRA_PROVIDER", "azure")
    # Force load_config to skip ./.env
    result = runner.invoke(cli, ["--env-file", str(tmp_path / "absent.env"), "status"])
    assert result.exit_code == 2
    assert "configuration error" in result.output.lower()


def test_status_with_no_state(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake_ssh_key: Path
) -> None:
    """status should be a no-op when terraform state doesn't exist."""
    monkeypatch.setenv("SSH_PUBLIC_KEY", str(fake_ssh_key))
    monkeypatch.chdir(tmp_path)  # no terraform/ dir → state_exists() == False
    (tmp_path / "terraform" / "vultr").mkdir(parents=True)

    result = runner.invoke(cli, ["--env-file", str(tmp_path / "absent.env"), "status"])
    assert result.exit_code == 0
    assert "nothing provisioned" in result.output.lower()


def test_destroy_no_state_short_circuits(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake_ssh_key: Path
) -> None:
    monkeypatch.setenv("SSH_PUBLIC_KEY", str(fake_ssh_key))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "terraform" / "vultr").mkdir(parents=True)

    result = runner.invoke(cli, ["--env-file", str(tmp_path / "absent.env"), "destroy", "--yes"])
    assert result.exit_code == 0
    assert "nothing to destroy" in result.output.lower()
