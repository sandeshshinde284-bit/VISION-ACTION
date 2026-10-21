data "google_storage_bucket_object_content" "gsn-psc-informations" {
  name   = "gsn-psc-informations"
  bucket = "gsn-informations"
}