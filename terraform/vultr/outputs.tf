output "server_ips" {
  description = "Public IPv4 of every provisioned node, in order."
  value       = [for n in vultr_instance.node : n.main_ip]
}

output "server_ids" {
  description = "Vultr instance IDs."
  value       = [for n in vultr_instance.node : n.id]
}

output "hostnames" {
  value = [for n in vultr_instance.node : n.hostname]
}
