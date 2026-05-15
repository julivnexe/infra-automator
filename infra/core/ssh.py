"""SSH helpers built on Paramiko.

Used by ``infra status`` for cheap reachability probes and by
``infra deploy`` to copy the compose stack + run ``docker compose up -d``.
Heavy lifting (full config management) is delegated to Ansible.
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko

from .logger import get_logger

log = get_logger()


@dataclass
class SshTarget:
    host: str
    user: str
    key_path: Path
    port: int = 22


def wait_for_port(host: str, port: int = 22, timeout: int = 180) -> bool:
    """Block until ``host:port`` accepts TCP connections, or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except OSError:
            time.sleep(3)
    return False


def _client(target: SshTarget) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=target.host,
        username=target.user,
        key_filename=str(target.key_path.expanduser()),
        port=target.port,
        timeout=15,
        allow_agent=True,
        look_for_keys=True,
    )
    return client


def run(target: SshTarget, command: str, check: bool = True) -> tuple[int, str, str]:
    """Run ``command`` on ``target``, returning (exit_code, stdout, stderr)."""
    log.debug("ssh %s@%s :: %s", target.user, target.host, command)
    with _client(target) as client:
        _stdin, stdout, stderr = client.exec_command(command, timeout=300)
        rc = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
    if check and rc != 0:
        raise RuntimeError(
            f"remote command failed (rc={rc}) on {target.host}: {command}\n--- stderr ---\n{err}"
        )
    return rc, out, err


def upload(target: SshTarget, local: Path, remote: str) -> None:
    log.debug("scp %s -> %s:%s", local, target.host, remote)
    with _client(target) as client, client.open_sftp() as sftp:
        sftp.put(str(local), remote)


def upload_tree(target: SshTarget, local_dir: Path, remote_dir: str) -> None:
    """Recursively upload a directory. Creates remote dirs as needed."""
    with _client(target) as client, client.open_sftp() as sftp:
        _mkdir_p(sftp, remote_dir)
        for path in local_dir.rglob("*"):
            rel = path.relative_to(local_dir).as_posix()
            remote_path = f"{remote_dir}/{rel}"
            if path.is_dir():
                _mkdir_p(sftp, remote_path)
            else:
                _mkdir_p(sftp, str(Path(remote_path).parent.as_posix()))
                sftp.put(str(path), remote_path)


def _mkdir_p(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts = remote_dir.strip("/").split("/")
    cur = ""
    for part in parts:
        cur = f"{cur}/{part}" if cur else f"/{part}"
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            sftp.mkdir(cur)
