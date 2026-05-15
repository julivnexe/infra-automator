# Architecture

## Components

```
                  +---------------------------+
                  |        infra (CLI)        |
                  |   Python / Click / Rich   |
                  +-------------+-------------+
                                |
              +-----------------+------------------+
              |                 |                  |
              v                 v                  v
       +-------------+   +-------------+    +-------------+
       |  Terraform  |   |   Ansible   |    |   SSH/SCP   |
       |  (vultr or  |   |  (harden.yml|    |  (paramiko) |
       |   DO stack) |   |   + roles)  |    |             |
       +------+------+   +------+------+    +------+------+
              |                 |                  |
              v                 v                  v
       +-------------+   +-------------+    +-------------+
       |  Cloud API  |   |   Servers   |    |  docker     |
       |  (provision)|   | (hardening) |    |  compose    |
       +-------------+   +-------------+    +-------------+
```

## Data flow per command

| Command         | Tool used         | State written                          |
| --------------- | ----------------- | -------------------------------------- |
| `infra up`      | Terraform         | `terraform/<provider>/terraform.tfstate`, `.infra/inventory.yml` |
| `infra harden`  | Ansible / SSH     | Remote — `/etc/ssh`, `/etc/ufw`, `/etc/fail2ban`, `/etc/docker` |
| `infra deploy`  | SSH + Docker      | Remote — `/opt/infra-app`, running containers |
| `infra status`  | SSH probes only   | None (read-only)                       |
| `infra destroy` | Terraform         | Removes `terraform.tfstate`, `.infra/inventory.yml` |

## Design decisions

**Why one CLI instead of separate scripts?**
A single binary is the only thing the user has to remember. The CLI itself is
a thin facade: every subcommand delegates to the right tool for the job
(Terraform for provisioning, Ansible for config, Docker Compose for runtime).

**Why shell out to Terraform instead of using `python-terraform` or HCL parsing?**
Terraform is the source of truth for cloud state. Re-implementing any part of
it in Python guarantees drift. The wrapper in `infra/core/terraform.py` is
deliberately ~150 LOC — it provides a typed interface to the binary, nothing more.

**Why both an Ansible playbook AND a shell script for hardening?**
Ansible is the right tool when it's available, but a bash-only fallback means
the project bootstraps cleanly on machines that don't have Ansible installed.
Both paths converge on the same end-state.

**Why local Terraform state in the portfolio version?**
A remote backend (S3, GCS, Terraform Cloud) is the right answer in production
but adds setup friction for a portfolio. The README documents how to swap in
a remote backend with one block change.

**Why two providers (Vultr + DigitalOcean)?**
To demonstrate that the abstraction holds — the Python layer has zero
provider-specific code; every stack exposes the same outputs (`server_ips`,
`server_ids`, `hostnames`). Adding Hetzner, Linode, or AWS is a matter of
writing a third `terraform/<name>/` stack.

**Why Docker Compose for the workload, not Kubernetes?**
Compose matches the footprint (1–3 nodes). Kubernetes would be theatre at
this scale. If the project grew past ~5 nodes, swapping to k3s or Nomad would
be a localised change in `deploy/`.
