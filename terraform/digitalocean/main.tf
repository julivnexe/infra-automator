locals {
  name_prefix = "infra-${var.env}"
  tags        = ["managed-by-infra-automator", "env-${var.env}"]
}

resource "digitalocean_ssh_key" "deploy" {
  name       = "${local.name_prefix}-deploy"
  public_key = var.ssh_public_key
}

resource "digitalocean_droplet" "node" {
  count = var.node_count

  name       = "${local.name_prefix}-${format("%02d", count.index + 1)}"
  region     = var.region
  size       = var.plan
  image      = var.image
  ssh_keys   = [digitalocean_ssh_key.deploy.fingerprint]
  ipv6       = true
  monitoring = true
  tags       = local.tags

  lifecycle {
    ignore_changes = [tags]
  }
}

resource "digitalocean_firewall" "default" {
  name = "${local.name_prefix}-fw"

  droplet_ids = [for d in digitalocean_droplet.node : d.id]

  # SSH — narrow further in production.
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "icmp"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
