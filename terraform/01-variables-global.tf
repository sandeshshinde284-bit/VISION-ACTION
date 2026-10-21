locals {
  project_ids = {
    "DEV"  = "gbr-mts-wgh-hkt-dev"
    "IACC" = "gbr-mts-wgh-hkt-iacc"
    "EACC" = "gbr-mts-wgh-hkt-eacc"
  }
  project_id      = local.project_ids[terraform.workspace]
  ss_project_id   = "fra-public-cloud-prod-shared-s"
  ss_vpc_id       = "projects/${local.ss_project_id}/global/networks/vpc-public-cloud-ss-prod-5"
  global_labels   = { for k, v in local.global_tags : replace(k, ":", "-") => replace(lower(v), " ", "-") if k != "wl:git:url" }
  billing_account = "015397-D13270-33BE00"
}
