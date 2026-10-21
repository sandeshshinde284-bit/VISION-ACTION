locals {
  gsn_address_space   = local.address_space != "" ? cidrsubnet(local.address_space, 28 - tonumber(split("/", local.address_space)[1]), 1) : ""
  gsn-region-selected = "europe-west9" # Fix your region (that must exist for GSN) europe-west9 is adviced
  # You can find the GCP GSN regions available in this documentation: https://confluence.worldline-solutions.com/display/PUB/Networking+-+GSN+services+subscription
  # In the "GCP GSN available regions" panel
  gsn-services-to-consume = [] # Put urls you need in this list
}