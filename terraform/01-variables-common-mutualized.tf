# from https://gitlab.kazan.myworldline.com/worldlineasacode/project-templates/mutualized-tf-vars
locals {
  application_service_prefix = replace(replace("MTS-WGH-HKT", " ", ""), "_", "-")

  application_service_by_env = {
    "DEV"  = "MTS-WGH-HKT"
    "IACC" = "MTS-WGH-HKT"
    "EACC" = "MTS-WGH-HKT"
  }
  application_service = local.application_service_by_env[terraform.workspace]
}

variable "region" {
  type        = string
  description = "The region where the core platform will be created"
  default     = "europe-west3"
}

variable "object_code" {
  type        = string
  description = "Object Code the project, in CI it is overrided automatically using TF_VAR_object_code_{terraform.workspace} env var"
  default     = ""
}

variable "project" {
  type        = string
  description = "Project Name"
  default     = "MTSWGHHKT"
}

variable "sid" {
  type        = string
  description = "Service Identifier."
  default     = ""
}

variable "sssd_secdom" {
  type        = string
  description = "SSSD SECDOM for SSH Access"
  default     = ""
}

# Define using env var TF_VAR_oscare_token
variable "oscare_token" {
  type        = string
  description = "Oscare API token"
  default     = "Ask CFLS/S.Bacquet" # https://confluence.worldline.com/pages/viewpage.action?pageId=329525581#Howtosendanalert?-Howtoobtainatoken?
  sensitive   = true
}

# Define using env var TF_VAR_oscare_secret
variable "oscare_secret" {
  type        = string
  description = "Oscare API secret corresponding to the above token"
  default     = "Ask CFLS/S.Bacquet" # https://confluence.worldline.com/pages/viewpage.action?pageId=329525581#Howtosendanalert?-Howtoobtainatoken?
  sensitive   = true
}

# Define using env var TF_VAR_git_url
variable "git_url" {
  type        = string
  description = "Terraform repo git URL"
  default     = "https://gitlab.kazan.myworldline.com/worldlineasacode/projects/gcp/MTS-WGH-HKT/MTS-WGH-HKT-Terraform"
}

locals {
  cmdb_environments = {
    "ADMIN"        = "Production"
    "ADMIN_PROD"   = "Production"
    "ADMIN_NOPROD" = "Internal Acceptance"
    "DEMO"         = "Demonstration"
    "DEV"          = "Development"
    "DRP"          = "Disater recovery"
    "IACC"         = "Internal Acceptance"
    "EACC"         = "External Acceptance"
    "PREPROD"      = "External Acceptance"
    "PROD"         = "Production"
    "STG"          = "Staging"
    "TEST"         = "Test"
    "TRAIN"        = "Training"
    "QA"           = "External Acceptance"
  }
  cmdb_environment = try(local.cmdb_environments[terraform.workspace], try(local.cmdb_environments[split("ADMIN_", terraform.workspace)[1]], "Development"))

  global_tags = {
    "wl:environment"      = terraform.workspace
    "wl:git:url"          = var.git_url
    "wl:cmdb"             = "true"
    "wl:cmdb:environment" = local.cmdb_environment
    "wl:cmdb:object-code" = var.object_code
    "poc:owner"           = "ShindeSandesh"
    "poc:name"            = "Vision-Action"
  }
}
