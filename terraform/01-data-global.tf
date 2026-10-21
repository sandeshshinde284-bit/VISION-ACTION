data "google_project" "project" {
}

# Fetch state from the foundational/base layer
# Fetch state from the foundational/base layer
data "google_storage_bucket_object_content" "sharedpocinfo" {
  name   = "base/DEV.tfstate"
  bucket = "tfstate-gbr-mts-wgh-hkt-dev"
}

locals {
  sharedpocinfo = jsondecode(data.google_storage_bucket_object_content.sharedpocinfo.content)
}

data "google_dns_managed_zone" "public_zone" {
  name = "gbr-mts-wgh-hkt-dev-dev-as8677-net" # Replace with the actual name of your manually created public zone in GCP
}

data "google_compute_network" "private_network" {
  name = local.sharedpocinfo.outputs.private_network.value.name
}

data "google_dns_managed_zone" "private_zone" {
  name = local.sharedpocinfo.outputs.private_zone.value.name
}
