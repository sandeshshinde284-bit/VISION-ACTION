locals {
  gw_tags = {
    owner  = "w114216"
    backup = "w114216"
    entity = "MTS-WGH-HKT"
    env    = local.cmdb_environment
  }
}

resource "time_rotating" "instance_admin_rotation" {
  rotation_days = 90
}

#Needed for each instance
resource "random_password" "instance_admin_password" {
  length           = 16
  special          = true
  override_special = "_$!%?&~#"
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
  keepers          = { time = time_rotating.instance_admin_rotation.id }
}

module "secure_tag_sql_gw" {
  source          = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/secure-tag.git?ref=1.1.0"
  apis            = local.sharedpocinfo.outputs.vm_apis.value #For old repo module.service-agents.apis
  project         = local.project_id
  private_network = data.google_compute_network.private_network.id
  name            = "sql-gw"
}

module "vm-patch-manager" {
  source  = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/vm-patch-manager.git?ref=0.1.1"
  project = local.project_id
  apis    = local.sharedpocinfo.outputs.vm_apis.value
  name    = "sql-gw-patch-${lower(terraform.workspace)}"
  recurring_schedule = {
    time_zone = "Europe/Paris"
    time_of_day = {
      hours   = 8
      minutes = 0
    }
    monthly = {
      day_of_week  = terraform.workspace == "PROD" ? "TUESDAY" : "MONDAY"
      week_ordinal = 1
    }
  }
}


#One gateway by project is needed
module "cloudsql-gateway" {
  source                        = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/cloudsql-gateway.git?ref=3.2.0"
  apis                          = local.sharedpocinfo.outputs.vm_apis.value
  dns_zone                      = data.google_dns_managed_zone.private_zone
  environment                   = terraform.workspace
  gateway_index                 = "01"
  gateway_tags                  = local.gw_tags
  gateway_subnetwork            = local.sharedpocinfo.outputs.vm_subnet_id.value
  application_service           = local.application_service # or var.object_code on old projects
  project                       = local.project_id
  region                        = var.region
  secdom                        = "DBA-HKT"
  osconfig_patch_deployment_id  = module.vm-patch-manager.patch_deployment_id
  secure_tags                   = [module.secure_tag_sql_gw.secure_tag]
  user_labels                   = local.global_labels
  enable_firewall_rules         = true
  network_firewall_requirements = local.sharedpocinfo.outputs.network_firewall_requirements.value
  gateway_firewall_ranges       = concat(module.public_cloud_vars.magellon_BON_ssh_gateways, module.public_cloud_vars.magellon_BON_rdp_gateways)
}



# Mysql, Postgres & SQLServer
# To avoid duplicating module in your backbone, use a for_each syntax as follow for example
# Example with a project having 3 environnements DEV, EACC, PROD

locals {
  instances = {
    DEV = {
      "01" = {
        database_version    = "POSTGRES_18"
        disk_type           = "PD_HDD"
        disk_size           = 10
        edition             = "ENTERPRISE"
        connectivity_method = "PSA"
        tier                = "db-custom-2-4096"
        trigram             = "hkt"
      }
    }
    EACC = {
      "01" = {
        param1 = "value"
      }
    }
    PROD = {
      "01" = {
        param1 = "value"
      }
    }
  }
  instance = local.instances[terraform.workspace]
}



module "cloudsql" {
  source              = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/cloudsql.git?ref=11.2.0"
  for_each            = local.instance
  application_service = local.application_service #You can use var.object_code if using an old repository
  environment         = terraform.workspace
  project             = local.project_id
  region              = var.region
  instance_index      = each.key
  database_version    = "POSTGRES_18"                            #Ex: POSTGRES_16 MYSQL_8_4 SQLSERVER_2022_STANDARD
  tier                = try(each.value.tier, "db-custom-2-4096") #Ex: db-custom-2-4096
  connectivity_method = try(each.value.connectivity_method, "PSA")
  disk_type           = try(each.value.disk_type, "PD_HDD") #Ex: PD_HDD
  disk_size           = try(each.value.disk_size, 10)       #Ex: 10
  private_network     = data.google_compute_network.private_network.id
  apis                = local.sharedpocinfo.outputs.vm_apis.value
  default_tags        = local.gw_tags
  password            = random_password.instance_admin_password.result
  dns_zone            = data.google_dns_managed_zone.private_zone
  user_labels         = local.global_labels

  #monitoring_requirements = module.monitoring-requirements
  gateway    = module.cloudsql-gateway
  subnetwork = local.sharedpocinfo.outputs.vm_subnet_id.value
  #record_client_address = false
  gateway_secure_tags           = [module.secure_tag_sql_gw.secure_tag]
  enable_firewall_rules         = true
  network_firewall_requirements = local.sharedpocinfo.outputs.network_firewall_requirements.value
  #Only useful for SQLServer
  #collation               = "<collation>" #Ex: SQL_Latin1_General_CP1_CI_AS, changing collation will need a rebuild
}
