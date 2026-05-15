"""Small utilities shared by command modules."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def which(name: str) -> str | None:
    return shutil.which(name)


def run_local(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a local command, streaming output. Returns exit code."""
    result = subprocess.run(cmd, cwd=cwd, check=False)
    return result.returncode


def human_table(rows: list[dict[str, str]]) -> str:
    """Minimal text table for environments where Rich isn't desirable."""
    if not rows:
        return "(empty)"
    headers = list(rows[0].keys())
    widths = {h: max(len(h), *(len(str(r.get(h, ""))) for r in rows)) for h in headers}
    line = "  ".join(h.ljust(widths[h]) for h in headers)
    sep = "  ".join("-" * widths[h] for h in headers)
    body = "\n".join("  ".join(str(r.get(h, "")).ljust(widths[h]) for h in headers) for r in rows)
    return f"{line}\n{sep}\n{body}"
