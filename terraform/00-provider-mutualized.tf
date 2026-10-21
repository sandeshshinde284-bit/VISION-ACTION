terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0.1"
    }
    gcsreferential = {
      source  = "public-cloud-wl/gcsreferential"
      version = "~> 1.0"
    }
    tools = {
      source  = "public-cloud-wl/tools"
      version = ">= 0.2.0"
    }
  }
}

provider "tools" {
}