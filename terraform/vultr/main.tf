locals {
  name_prefix = "infra-${var.env}"
  tags        = ["managed-by:infra-automator", "env:${var.env}"]
}

resource "vultr_ssh_key" "deploy" {
  name    = "${local.name_prefix}-deploy"
  ssh_key = var.ssh_public_key
}

resource "vultr_instance" "node" {
  count = var.node_count

  hostname    = "${local.name_prefix}-${format("%02d", count.index + 1)}"
  label       = "${local.name_prefix}-${format("%02d", count.index + 1)}"
  plan        = var.plan
  region      = var.region
  os_id       = var.os_id
  ssh_key_ids = [vultr_ssh_key.deploy.id]
  enable_ipv6 = true
  backups     = "disabled"
  tags        = local.tags

  # Don't tear the instance down if the user later changes labels/tags.
  lifecycle {
    ignore_changes = [tags, label]
  }
}
