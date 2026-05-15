# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Roadmap items tracked in [README.md#roadmap](README.md#roadmap).

## [0.1.0] — 2026-05-14

### Added

- `infra` CLI with `up`, `harden`, `deploy`, `status`, `destroy` commands.
- Terraform stacks for **Vultr** and **DigitalOcean** with a shared output contract.
- Ansible playbook + roles for baseline hardening (common, ssh, firewall, fail2ban, docker).
- Pure-bash hardening fallback (`scripts/harden.sh`) for Ansible-free environments.
- Docker Compose sample stack: nginx → FastAPI app, with healthchecks and log rotation.
- GitHub Actions: `ci`, `security`, `release` workflows; Dependabot.
- pytest suite covering config parsing, CLI wiring, and the Terraform wrapper.
- Pre-commit config: ruff, black, terraform fmt, secret detection.
