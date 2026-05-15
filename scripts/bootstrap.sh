#!/usr/bin/env bash
# Local dev bootstrap. Sets up venv + installs the CLI in editable mode.
set -euo pipefail

if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "[bootstrap] copied .env.example -> .env (edit it before running 'infra up')"
fi

echo "[bootstrap] done — run: source .venv/bin/activate && infra --help"
