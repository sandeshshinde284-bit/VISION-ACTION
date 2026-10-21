# ==============================================================================
# PROJECT V.I.S.I.O.N. - AUTOMATED DATA SYNCHRONIZATION SCHEDULER (Phase 4)
# ==============================================================================
# File Description:
# This module automates the background delta crawls for Atlassian Confluence 
# and Azure DevOps tickets natively inside Terraform. It dynamically reads
# the deployed Cloud Run Backend url, triggers a POST sync call every 3 hours,
# and signs requests securely with OpenID Connect (OIDC) Service Account tokens.
# ==============================================================================

locals {
  # Workaround for Terraform inconsistent final plan error:
  # Force backend_service_uri to be "known after apply" during the plan phase
  # by making it conditional on network_endpoint_group_id, which is computed during apply.
  backend_service_uri = module.vision-backend-cloud-run-service.network_endpoint_group_id == "" ? "" : module.vision-backend-cloud-run-service.service_uri
}

resource "google_cloud_scheduler_job" "vision_sync_scheduler" {
  project     = local.project_id
  name        = "vision-confluence-sync-scheduler"
  region      = var.region
  description = "Automated 3-Hour Delta Synchronization Scheduler for Confluence and ADO"
  schedule    = "0 */3 * * *"  # Every 3 hours
  time_zone   = "Europe/Paris" # Standard Magellon TZ

  http_target {
    uri         = "${local.backend_service_uri}/api/sync" # DYNAMIC CLOUD RUN URL!
    http_method = "POST"
    body        = base64encode(jsonencode({})) # Empty JSON body

    oidc_token {
      service_account_email = module.test_sa.email      # Secure Service Account OIDC signature!
      audience              = local.backend_service_uri # Explicitly set audience to prevent inconsistent plan error!
    }

    headers = {
      "Content-Type" = "application/json"
    }
  }
  depends_on = [module.vision-backend-cloud-run-service]
}
