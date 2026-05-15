"""Tiny FastAPI sample app — proves the deploy pipeline works end-to-end."""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="infra-automator sample app", version="0.1.0")


@app.get("/")
def index() -> dict[str, str]:
    return {
        "service": "infra-automator-sample",
        "hostname": socket.gethostname(),
        "env": os.getenv("APP_ENV", "unknown"),
        "now": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
