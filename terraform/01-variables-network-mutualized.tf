# from https://gitlab.kazan.myworldline.com/worldlineasacode/project-templates/mutualized-tf-vars

locals {

  address_spaces = {

    "DEV" = "10.134.188.0/24"

    "IACC" = "10.134.189.0/24"

    "EACC" = "10.134.197.0/24"

  }
  address_space = try(local.address_spaces[terraform.workspace], "")

}
