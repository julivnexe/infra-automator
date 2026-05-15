<div align="center">

# infra-automator

**One opinionated CLI to provision, harden, deploy, and destroy small cloud footprints.**

`infra up` → `infra harden` → `infra deploy` → `infra status` → `infra destroy`

[![CI](https://img.shields.io/github/actions/workflow/status/julivnexe/infra-automator/ci.yml?branch=main&label=ci)](.github/workflows/ci.yml)
[![Security](https://img.shields.io/github/actions/workflow/status/julivnexe/infra-automator/security.yml?branch=main&label=security)](.github/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Terraform](https://img.shields.io/badge/terraform-%E2%89%A51.5-7B42BC)](terraform/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## Why this exists

Spinning up a hardened, app-ready Linux box on a fresh cloud account is a
solved problem — but the solution is usually spread across five tools and a
README full of copy-paste. `infra-automator` collapses that into one CLI
backed by **Terraform, Ansible, and Docker Compose**, each doing the part
of the job it's actually good at.

The repo doubles as a portfolio piece: it demonstrates IaC, configuration
management, container deployment, CI/CD, security scanning, and clean Python
packaging — wired together the way a working DevOps engineer would do it.

---

## Highlights

- 🛰  **Multi-cloud provisioning** — Vultr + DigitalOcean, swappable with one env var
- 🛡  **Baseline hardening** — non-root admin, key-only SSH, UFW, fail2ban, unattended upgrades, Docker installed
- 🚢  **Docker Compose deploys** — sync a stack to every node and bring it up with one command
- 📊  **Live status board** — Rich-rendered table of every node, SSH reachability, container count, disk usage
- ♻️  **Idempotent everywhere** — Terraform state, Ansible roles, and shell fallbacks all safe to re-run
- 🧪  **Real CI** — ruff + black + mypy + pytest + terraform fmt/validate + ansible-lint + shellcheck + tfsec + trivy
- 📦  **Installable Python package** — `pip install -e .` gives you the `infra` command
- 🔐  **No secrets on disk** — credentials live in `.env`, passed to Terraform via `TF_VAR_*`

---

## Architecture

```
                  +---------------------------+
                  |        infra (CLI)        |
                  |   Python · Click · Rich   |
                  +-------------+-------------+
                                |
              +-----------------+------------------+
              |                 |                  |
              v                 v                  v
       +-------------+   +-------------+    +-------------+
       |  Terraform  |   |   Ansible   |    |   SSH/SCP   |
       |  vultr / DO |   | harden.yml  |    |  (paramiko) |
       +------+------+   +------+------+    +------+------+
              |                 |                  |
              v                 v                  v
       +-------------+   +-------------+    +-------------+
       |  Cloud API  |   |   Servers   |    |   docker    |
       | (provision) |   | (hardening) |    |   compose   |
       +-------------+   +-------------+    +-------------+
```

A deeper write-up — including data flow per command and the design
trade-offs — lives in [`docs/architecture.md`](docs/architecture.md).

---

## Roadmap coverage

| Capability                                | Implementation                                                                     | Status |
| ----------------------------------------- | ---------------------------------------------------------------------------------- | :----: |
| Multi-cloud provisioning                  | `terraform/vultr/`, `terraform/digitalocean/`                                      |   ✅   |
| Idempotent server hardening               | `ansible/harden.yml` + roles, shell fallback in `scripts/harden.sh`                |   ✅   |
| Key-only SSH on configurable port         | `ansible/roles/ssh/`                                                               |   ✅   |
| Host firewall (deny-by-default)           | `ansible/roles/firewall/` (UFW) + DigitalOcean cloud firewall                      |   ✅   |
| Brute-force protection                    | `ansible/roles/fail2ban/`                                                          |   ✅   |
| Container runtime install                 | `ansible/roles/docker/` (Docker CE + compose plugin + log rotation)                |   ✅   |
| Docker Compose deploy pipeline            | `infra/commands/deploy.py` + `deploy/`                                             |   ✅   |
| Live status reporting                     | `infra/commands/status.py` (Rich table)                                            |   ✅   |
| Safe teardown                             | `infra/commands/destroy.py` (confirms, clears local state)                         |   ✅   |
| CI (lint, types, tests, IaC validate)     | `.github/workflows/ci.yml`                                                         |   ✅   |
| Security scanning (deps, IaC, FS)         | `.github/workflows/security.yml` (pip-audit, tfsec, trivy)                         |   ✅   |
| Container image release pipeline          | `.github/workflows/release.yml` (GHCR, multi-arch)                                 |   ✅   |
| Dependency upkeep                         | `.github/dependabot.yml`                                                           |   ✅   |
| Remote Terraform backend                  | Documented in [Day-2 ops](#day-2-operations); local state by default               |   📋   |
| TLS termination (Let's Encrypt)           | Roadmap                                                                            |   ⏭️   |
| Centralised logging / metrics             | Roadmap (Loki/Promtail role)                                                       |   ⏭️   |

---

## Project layout

```
infra-automator/
├── infra/                       # Python package — installable as `infra`
│   ├── cli.py                   #   Click entry point
│   ├── commands/                #   up · harden · deploy · status · destroy
│   ├── core/                    #   config · terraform wrapper · ssh · logger
│   └── utils/
├── terraform/
│   ├── vultr/                   # Vultr stack — SSH key + N instances
│   └── digitalocean/            # DO stack — SSH key + N droplets + firewall
├── ansible/
│   ├── harden.yml               # Main playbook
│   └── roles/                   # common · ssh · firewall · fail2ban · docker
├── scripts/
│   ├── harden.sh                # Ansible-free hardening fallback
│   └── bootstrap.sh             # Local dev bootstrap (venv + deps)
├── deploy/
│   ├── docker-compose.yml       # Sample stack: nginx → FastAPI sample-app
│   ├── nginx/nginx.conf
│   └── apps/sample-app/         # Tiny FastAPI image
├── tests/                       # pytest — config, CLI, terraform wrapper
├── .github/workflows/           # ci · release · security
├── docs/                        # architecture.md (+ screenshots placeholder)
├── pyproject.toml · Makefile · requirements*.txt · .env.example
└── README.md
```

---

## Quickstart

### 1. Prerequisites

| Tool          | Version  | Why                          |
| ------------- | -------- | ---------------------------- |
| Python        | ≥ 3.10   | Runs the CLI                 |
| Terraform     | ≥ 1.5    | Provisioning                 |
| Ansible       | ≥ 2.15   | (Optional — shell fallback)  |
| SSH keypair   | ed25519  | Auth to provisioned nodes    |
| Cloud account | Vultr **or** DigitalOcean | At least one API token |

### 2. Install

```bash
git clone https://github.com/julivnexe/infra-automator.git
cd infra-automator
./scripts/bootstrap.sh         # creates .venv, installs deps, copies .env
source .venv/bin/activate
infra --help
```

### 3. Configure

```bash
cp .env.example .env
$EDITOR .env                   # set VULTR_API_KEY or DIGITALOCEAN_TOKEN
```

Minimum set of values to fill in:

```dotenv
INFRA_PROVIDER=vultr
VULTR_API_KEY=vlt_xxx
SSH_PUBLIC_KEY=~/.ssh/id_ed25519.pub
SSH_PRIVATE_KEY=~/.ssh/id_ed25519
ADMIN_USER=deploy
```

### 4. Run the full lifecycle

```bash
infra up               # Provision (~60s)
infra harden           # Apply baseline hardening (~3 min)
infra deploy           # Push the compose stack (~30s)
infra status           # Show the live state
# ...do your thing...
infra destroy --yes    # Tear it all down
```

Every command is idempotent — re-running `up` after a config change applies
the diff; re-running `harden` is a no-op when nothing has drifted.

---

## Command reference

### `infra up`

Provisions servers via Terraform using the configured provider. Waits for
SSH to come up, then writes an Ansible inventory to `.infra/inventory.yml`.

```bash
infra up [--yes] [--skip-wait]
```

### `infra harden`

Applies baseline security hardening. Prefers `ansible-playbook` if it's on
PATH; falls back to `scripts/harden.sh` over SSH otherwise.

```bash
infra harden [--force-shell]
```

End-state after hardening:

- Non-root `${ADMIN_USER}` with passwordless sudo and your SSH key
- SSH: key-only, root login disabled, configurable port, `AllowUsers` allowlist
- UFW: `default deny incoming`, allow 22/80/443 + extras, `limit` on SSH
- fail2ban watching sshd (`maxretry 4`, `bantime 1h`)
- Unattended security upgrades enabled
- Docker CE + compose plugin installed, with `live-restore` and 10MB×3 log rotation

### `infra deploy`

Uploads `./deploy/` to every node and runs `docker compose up -d`. Pulls
images first by default; pass `--no-pull` to skip.

```bash
infra deploy [--stack PATH] [--pull/--no-pull]
```

### `infra status`

Prints a Rich table — SSH reachability, uptime, container count, disk
usage per node.

```bash
infra status
```

```
                 infra-automator — vultr/dev
┏━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┓
┃ Host           ┃ SSH ┃ Uptime                 ┃ Containers ┃ Disk ┃
┡━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━┩
│ 203.0.113.10   │  ✓  │ up 14 minutes          │          2 │  3%  │
│ 203.0.113.11   │  ✓  │ up 14 minutes          │          2 │  3%  │
└────────────────┴─────┴────────────────────────┴────────────┴──────┘
```

### `infra destroy`

Confirms, then runs `terraform destroy`. Removes `.infra/inventory.yml`.

```bash
infra destroy [--yes]
```

---

## Design decisions

**One CLI, not five scripts.** A single entry point keeps the cognitive
surface tiny. Each subcommand delegates to the right tool for the job
(Terraform / Ansible / Docker), so we benefit from each tool's maturity
without papering over it.

**Shell out to Terraform.** Re-implementing any part of Terraform in
Python is a path to drift. The wrapper at
[`infra/core/terraform.py`](infra/core/terraform.py) is a thin typed facade
over the binary.

**Two providers, one interface.** Every Terraform stack exposes the same
outputs (`server_ips`, `server_ids`, `hostnames`). Adding Hetzner / Linode
/ AWS is a matter of writing a third `terraform/<name>/` stack — no Python
changes.

**Ansible-or-shell hardening.** Ansible is the right tool, but the shell
fallback means the project bootstraps cleanly even on a machine that
doesn't have Ansible installed. Both paths converge on the same end-state.

**Secrets via env vars, never `.tfvars`.** Provider credentials are
exported as `TF_VAR_*` at the moment of `terraform apply`. Nothing
sensitive ends up on disk or in state.

**Docker Compose, not Kubernetes.** Compose matches the 1–3 node target.
Kubernetes at this scale would be theatre. If the project grew past
~5 nodes, swapping to k3s or Nomad would be a localised change in
`deploy/`.

---

## Day-2 operations

### Switching cloud providers

```bash
sed -i 's/^INFRA_PROVIDER=.*/INFRA_PROVIDER=digitalocean/' .env
infra up    # uses terraform/digitalocean/
```

### Re-running hardening after a config change

`infra harden` is safe to re-run. Both the Ansible playbook and the shell
script are idempotent. To skip a single role (e.g. fail2ban) when running
Ansible directly:

```bash
ansible-playbook -i .infra/inventory.yml ansible/harden.yml --skip-tags fail2ban
```

### Switching to a remote Terraform backend

Local state is fine for one-engineer portfolio use. For a real team,
drop a `backend` block into `terraform/<provider>/versions.tf`:

```hcl
terraform {
  backend "s3" {
    bucket = "my-tfstate"
    key    = "infra-automator/vultr.tfstate"
    region = "us-east-1"
  }
}
```

Then `terraform init -migrate-state` once.

### Adding a new provider

1. Create `terraform/<name>/{versions,variables,main,outputs}.tf`.
2. Make sure outputs include `server_ips` (list of strings).
3. Add `<name>` to `PROVIDERS` in `infra/core/config.py`.
4. Teach `infra/core/terraform.py::_env_for` how to pass the credential.

### Adding a new app to the deploy stack

Drop it into `deploy/apps/<your-app>/`, reference it from
`deploy/docker-compose.yml`, then `infra deploy`.

### Rotating the admin SSH key

Update `SSH_PUBLIC_KEY` in `.env`, then `infra harden`. The `common` role
overwrites `authorized_keys` from the seed key on every run.

---

## Development

```bash
make install-dev       # editable install + dev deps
make lint              # ruff
make format            # black + ruff --fix
make typecheck         # mypy
make test              # pytest with coverage
make check             # all of the above
pre-commit install     # run hooks on every commit
```

### CI

Three workflows run on every PR + push to `main`:

| Workflow         | What it does                                                                |
| ---------------- | --------------------------------------------------------------------------- |
| `ci.yml`         | ruff · black · mypy · pytest (3.10/3.11/3.12) · terraform fmt+validate · ansible-lint · shellcheck |
| `security.yml`   | pip-audit · tfsec · trivy (SARIF → GitHub Code Scanning)                    |
| `release.yml`    | On version tags: build sdist+wheel, attach to release, push multi-arch sample-app image to GHCR |

### Tests

```bash
pytest                  # whole suite
pytest tests/test_cli.py -v
pytest -k status        # by keyword
```

---

## Screenshots

<!-- Drop terminal recordings / PNGs into docs/images/ and reference them here. -->

| `infra up`              | `infra status`              |
| ----------------------- | --------------------------- |
| ![up](docs/images/up.png) | ![status](docs/images/status.png) |

---

## Roadmap

- [ ] TLS termination with Let's Encrypt (Caddy or certbot role)
- [ ] Centralised logging — Promtail → Loki role
- [ ] Optional Tailscale/WireGuard mesh between nodes
- [ ] `infra backup` — encrypted volume snapshots via provider API
- [ ] Hetzner Cloud and Linode/Akamai stacks
- [ ] Migration path to k3s for >5 node fleets

---

## License

MIT — see [LICENSE](LICENSE).

> Built as a portfolio project to demonstrate IaC, configuration
> management, and end-to-end DevOps practices. Not a substitute for a
> hardened production platform; use it as a starting point.
