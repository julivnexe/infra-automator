terraform {
  required_version = ">= 1.5"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.40"
    }
  }
}

# The provider reads DIGITALOCEAN_TOKEN from the environment, set by the CLI.
provider "digitalocean" {
  token = var.do_token
}
