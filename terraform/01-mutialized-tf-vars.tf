module "public_cloud_vars" {
  source          = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/wl-public-cloud-vars.git?ref=master"
  connection_type = "INTERCO"
}