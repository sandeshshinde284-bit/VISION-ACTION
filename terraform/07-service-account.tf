module "test_sa" {
  source              = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/service-account.git?ref=3.0.0"
  name                = "vision-action"
  project             = local.project_id
  application_service = local.application_service #You can use var.object_code if using an old repository
  roles = [
    "roles/cloudtranslate.user",
    "roles/aiplatform.user",
    "roles/run.invoker",
    "roles/secretmanager.secretAccessor"
  ]
  job_titles = ["cloud-engineer", "system-support", "integrator"]
}
