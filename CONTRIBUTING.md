# Contributing

Thanks for taking a look! This project is a portfolio piece but PRs are
welcome.

## Setup

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
pre-commit install
```

## Before opening a PR

```bash
make check
```

Which runs ruff, black, mypy, and the pytest suite. CI runs the same checks
plus terraform fmt/validate, ansible-lint, shellcheck, and security scans.

## Conventions

- **Commits**: short imperative subject (`fix terraform output parsing`),
  one logical change per commit.
- **Branches**: `feat/<thing>`, `fix/<thing>`, `chore/<thing>`.
- **Python**: type hints on every public function; comments only where the
  *why* is non-obvious. Don't comment what the code already says.
- **Terraform**: every stack must export the same outputs (`server_ips`,
  `server_ids`, `hostnames`) — that's the contract the Python layer relies on.
- **Ansible**: idempotency is non-negotiable. If a task isn't idempotent,
  it's a bug.
- **Shell**: `set -euo pipefail`, shellcheck-clean.

## Adding a provider

See the [Day-2 ops](README.md#adding-a-new-provider) section of the README.

## Reporting security issues

Please open a private GitHub Security Advisory rather than a public issue.
