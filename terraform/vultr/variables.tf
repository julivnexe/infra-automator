variable "vultr_api_key" {
  type        = string
  description = "Vultr API key. Sourced from TF_VAR_vultr_api_key by the CLI."
  sensitive   = true
}

variable "env" {
  type        = string
  description = "Logical environment name (used in tags + hostnames)."
  default     = "dev"
}

variable "region" {
  type        = string
  description = "Vultr region slug (ewr, lax, fra, ...)."
  default     = "ewr"
}

variable "plan" {
  type        = string
  description = "Vultr plan slug (e.g. vc2-1c-1gb)."
  default     = "vc2-1c-1gb"
}

variable "node_count" {
  type        = number
  description = "Number of identical nodes to provision."
  default     = 1

  validation {
    condition     = var.node_count >= 1 && var.node_count <= 10
    error_message = "node_count must be between 1 and 10."
  }
}

variable "ssh_public_key" {
  type        = string
  description = "OpenSSH-format public key, injected into each node's authorized_keys."
}

variable "os_id" {
  type        = number
  description = "Vultr OS ID. 1743 == Ubuntu 22.04 x64."
  default     = 1743
}
