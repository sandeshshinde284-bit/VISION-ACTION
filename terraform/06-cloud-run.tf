###################################################################
# You must first create your certificates and your certificate map #
###################################################################

locals {
  app_url_prefixs = ["vision-action"]
  app_urls        = { for url in local.app_url_prefixs : (url) => trimsuffix("${url}.${data.google_dns_managed_zone.public_zone.dns_name}", ".") }
}

resource "google_certificate_manager_certificate_map" "vision_action" {
  name        = "xlb-l7-${lower(terraform.workspace)}-vision-action"
  description = "Certificate Map for Vision-Action Load Balancer"
}

######################################################
# Using existing DNS managed zone from shared states #
######################################################

module "public_certificate" {
  for_each        = toset(local.app_url_prefixs)
  source          = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/public-certificate.git?ref=0.1.1"
  project         = local.project_id
  apis            = local.sharedpocinfo.outputs.vm_apis.value
  domains         = [trimsuffix("${each.key}.${data.google_dns_managed_zone.public_zone.dns_name}", ".")]
  managed_zone    = data.google_dns_managed_zone.public_zone.name
  certificate_map = google_certificate_manager_certificate_map.vision_action.name
}

# Frontend Cloud Run Service
module "vision-frontend-cloud-run-service" {
  source              = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/cloud-run-service.git?ref=1.2.0"
  project             = local.project_id
  name                = "vision-action-frontend"
  apis                = local.sharedpocinfo.outputs.vm_apis.value
  application_service = local.application_service
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  vpc_connector       = local.sharedpocinfo.outputs.vpc_connector.value
  labels              = local.global_labels

  region                 = var.region
  invoker_iam_disabled   = true
  service_account        = module.test_sa.email
  service_account_create = false
  min_instance_count     = 0
  max_instance_count     = 3
  containers = {
    default = {
      image = "europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-frontend:v1.5.0"
    }
  }
}

# --- GOOGLE SECRET MANAGER SLOTS FOR EXPIRING TOKENS (Phase 4 - Security Hardened) ---
resource "google_secret_manager_secret" "confluence_api_token" {
  project   = local.project_id
  secret_id = "confluence-api-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "confluence_api_token_val" {
  secret      = google_secret_manager_secret.confluence_api_token.id
  secret_data = "placeholder" # Set to empty/placeholder. Sandesh will update via GCP UI!
}

resource "google_secret_manager_secret" "ado_pat_token" {
  project   = local.project_id
  secret_id = "ado-pat-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "ado_pat_token_val" {
  secret      = google_secret_manager_secret.ado_pat_token.id
  secret_data = "placeholder" # Set to empty/placeholder. Sandesh will update via GCP UI!
}

resource "google_secret_manager_secret" "db_password" {
  project   = local.project_id
  secret_id = "vision-db-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password_val" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.instance_admin_password.result # Automatically syncs generated SQL password!
}

# Backend Cloud Run Service
module "vision-backend-cloud-run-service" {
  source              = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/cloud-run-service.git?ref=1.2.0"
  project             = local.project_id
  name                = "vision-action-backend"
  apis                = local.sharedpocinfo.outputs.vm_apis.value
  application_service = local.application_service
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  vpc_connector       = local.sharedpocinfo.outputs.vpc_connector.value
  labels              = local.global_labels

  region                 = var.region
  invoker_iam_disabled   = true
  service_account        = module.test_sa.email
  service_account_create = false
  min_instance_count     = 0 
  max_instance_count     = 3
  default_uri_disabled   = false
  vpc_connector_egress   = "PRIVATE_RANGES_ONLY" # Fixes Confluence Timeout instantly by only routing Private IPs via VPC!

  containers = {
    default = {
      image = "europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-backend:v1.6.0" 
      env = {
        DATABASE_TARGET   = { value = "CLOUD" }
        PG_HOST           = { value = "pgdmtswghhkt01g.dev.mtswghhkt.gcp.meshcore.net" }
        PG_PORT           = { value = "5432" }
        PG_DATABASE       = { value = "postgres" } # Your active database name
        PG_USER           = { value = "postgres" } # Your Terraform SQL User Account!
        CONFLUENCE_URL    = { value = "https://worldline.atlassian.net" } # Removed /wiki suffix!
        CONFLUENCE_SPACES = { value = "WLMTSConsole,PROJWT,Genoa Kiosk,Dagobah,ERK,OASIS" } # Your active synced Confluence spaces!
        ADO_URL           = { value = "https://dev.azure.com/worldline" }
        ADO_ORGANIZATION  = { value = "worldline" }
        ADO_PROJECT       = { value = "Genoa Rail Kiosk,WLMTSConsole" } # Your actual active production ADO project boards!
        GCP_PROJECT_ID    = { value = local.project_id }
        GCP_LOCATION      = { value = var.region }
        DEFAULT_ADMIN_NAME = { value = "Sandesh" }
        RAG_MAX_CONTEXT_CHARS = { value = "30000" }
        RAG_MAX_LINK_DEPTH = { value = "3" }
      }
      secrets = {
        PG_PASSWORD = {
          secret  = google_secret_manager_secret.db_password.secret_id
          version = "latest"
        }
        CONFLUENCE_PAT = {
          secret  = google_secret_manager_secret.confluence_api_token.secret_id
          version = "latest"
        }
        ADO_PAT = {
          secret  = google_secret_manager_secret.ado_pat_token.secret_id
          version = "latest"
        }
      }
    }
  }
}

resource "google_compute_url_map" "vision_action" {
  project         = local.project_id
  name            = "xlb-l7-${lower(terraform.workspace)}-vision-action"
  default_service = module.vision_action_xlb_l7.backend_services["vision-frontend-backend"].id

  host_rule {
    hosts        = [local.app_urls["vision-action"]]
    path_matcher = "all-paths"
  }

  path_matcher {
    name            = "all-paths"
    default_service = module.vision_action_xlb_l7.backend_services["vision-frontend-backend"].id

    path_rule {
      paths   = ["/api", "/api/*", "/ws", "/ws/*"]
      service = module.vision_action_xlb_l7.backend_services["vision-api-backend"].id
    }
  }
}

module "vision_action_xlb_l7" {
  source          = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/load-balancing/external-global-application-lb.git?ref=0.4.1"
  project         = local.project_id
  name            = "xlb-l7-${lower(terraform.workspace)}-vision-action"
  url_map         = google_compute_url_map.vision_action.id
  ssl_policy      = local.sharedpocinfo.outputs.ssl_policy_id.value
  apis            = local.sharedpocinfo.outputs.vm_apis.value
  certificate_map = google_certificate_manager_certificate_map.vision_action.id
  security_policy = "default-security-policy-for-backend-service-afc-transit-backend"
  labels          = local.global_labels
  depends_on = [
    module.vision-frontend-cloud-run-service,
    module.vision-backend-cloud-run-service
  ]
  dns_records = [
    {
      dns_managed_zone = data.google_dns_managed_zone.public_zone
      records          = values(local.app_urls)
    }
  ]
  backend_services = {
    vision-frontend-backend = {
      protocol  = "HTTP"
      port_name = "http"
      backends  = [{ group = module.vision-frontend-cloud-run-service.network_endpoint_group_id }]
    }
    vision-api-backend = {
      protocol  = "HTTP"
      port_name = "http"
      backends  = [{ group = module.vision-backend-cloud-run-service.network_endpoint_group_id }]
    }
  }
}

data "google_dns_managed_zone" "public_zone" {
  project = local.ss_project_id
  name    = local.sharedpocinfo.outputs.public_zone.value.name
}

data "google_dns_managed_zone" "private_zone" {
  project = local.ss_project_id
  name    = local.sharedpocinfo.outputs.private_zone.value.name
}
