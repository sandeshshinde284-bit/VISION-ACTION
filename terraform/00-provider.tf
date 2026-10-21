provider "google" {
  project        = local.project_id
  region         = var.region
  default_labels = local.global_labels
}

# provider "google-beta" {
#   project        = local.project_id
#   region         = var.region
#   default_labels = local.global_labels
# }

provider "google" {
  project               = local.project_id
  region                = var.region
  user_project_override = true
  billing_project       = local.project_id
  alias                 = "custom"
  default_labels        = local.global_labels
}

provider "gcsreferential" {
  referential_bucket = "tfstate-${local.project_id}"
}
