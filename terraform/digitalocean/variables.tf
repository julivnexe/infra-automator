variable "do_token" {
  type        = string
  description = "DigitalOcean personal access token."
  sensitive   = true
}

variable "env" {
  type    = string
  default = "dev"
}

variable "region" {
  type    = string
  default = "nyc3"
}

variable "plan" {
  type        = string
  description = "DigitalOcean droplet size slug (e.g. s-1vcpu-1gb)."
  default     = "s-1vcpu-1gb"
}

variable "node_count" {
  type    = number
  default = 1

  validation {
    condition     = var.node_count >= 1 && var.node_count <= 10
    error_message = "node_count must be between 1 and 10."
  }
}

variable "ssh_public_key" {
  type = string
}

variable "image" {
  type        = string
  description = "DigitalOcean image slug."
  default     = "ubuntu-22-04-x64"
}
