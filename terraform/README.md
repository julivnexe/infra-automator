# terraform/

Two interchangeable stacks. The CLI picks one based on `INFRA_PROVIDER`:

| Stack             | Provider             | Resources                              |
| ----------------- | -------------------- | -------------------------------------- |
| `vultr/`          | vultr/vultr ~> 2.21  | SSH key, N×`vultr_instance`            |
| `digitalocean/`   | digitalocean ~> 2.40 | SSH key, N×`digitalocean_droplet`, firewall |

Both stacks export the same outputs (`server_ips`, `server_ids`, `hostnames`)
so the Python layer can treat them as a single interface.

Credentials are injected at runtime via `TF_VAR_*` env vars — never stored
in `.tfvars` files. State stays local for portfolio use; for a real
multi-engineer setup, point `terraform { backend "s3" { … } }` at remote
state.
