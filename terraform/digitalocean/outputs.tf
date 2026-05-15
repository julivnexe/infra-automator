output "server_ips" {
  description = "Public IPv4 of every droplet, in order."
  value       = [for d in digitalocean_droplet.node : d.ipv4_address]
}

output "server_ids" {
  value = [for d in digitalocean_droplet.node : d.id]
}

output "hostnames" {
  value = [for d in digitalocean_droplet.node : d.name]
}
