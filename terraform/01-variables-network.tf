variable "manage_svc_address_space" {
  description = "Manages Services Address Space"
  type        = string
  default     = "10.102.16.0/20"
}

locals {
  # Be careful address space need to be a /24 or bigger

  # Splitting the address space in 2 and taking the 2nd one for VM address space
  vm_address_space = local.address_space != "" ? cidrsubnet(local.address_space, 1, 1) : ""

  # Taking the 1st /28 for VPC Connector address space
  vpc_connector_address_space = local.address_space != "" ? cidrsubnet(local.address_space, 28 - tonumber(split("/", local.address_space)[1]), 0) : ""
  # Taking the 2nd /26 for internal loadbalancer if needed
  internal_lb_address_space = local.address_space != "" ? cidrsubnet(local.address_space, 26 - tonumber(split("/", local.address_space)[1]), 1) : ""
}