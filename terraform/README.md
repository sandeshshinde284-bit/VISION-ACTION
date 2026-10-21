# Description

This is the standard terraform repository for 

All new GCP projects created are now being delivered with 2 different gitlab repositories :

- 1 gitlab repository refered as ADMIN MTSWGHHKT-ADMIN-Terraform which will be owning only GCP services api activation, financial alerts (budgets), email notifications, and users permissions management.

- 1 gitlab repository refered as standard MTSWGHHKT-Terraform (this one) where you will manage your main cloud resources as you were doing before (vm, gke, cloudsql creation/update/deletion...)

The aim of this change is to allow a smoother user experience by avoiding undeterministic dependencies errors during terraform resources deployment / update / deletion. This should allow essentially a better capacity to destroy your environment (like GKE dev clusters)

This standard terraform repository will contain all the cloud components of your platform : GKE clusters, cloudSQL, VMs...

# Useful links

## GCP Quickstart

Documentation about how to start your project on GCP: [https://confluence.worldline-solutions.com/display/PUB/GCP+Quickstart](https://confluence.worldline-solutions.com/display/PUB/GCP+Quickstart)

## Magellon terraform modules

Terraform community modules for GCP, coded and provided by Magellon:
<a href="https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp" target="_blank">ccc/terraform/modules/gcp</a>

## Magellon terraform guidelines

Documentation about terraform within Magellon: [https://confluence.worldline-solutions.com/display/PUB/Terraform](https://confluence.worldline-solutions.com/display/PUB/Terraform)

## Magellon GCP guidelines

Documentation about GCP and Magellon guidelines: [https://confluence.worldline-solutions.com/display/PUB/GCP](https://confluence.worldline-solutions.com/display/PUB/GCP)

## Terraform and GCP provider

Official Terraform provider for GCP: [https://registry.terraform.io/providers/hashicorp/google/latest/docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

## Terraform CI/CD pipelines

Kazan community GitLab CI/CD pipeline template for terraform documentation: 
<a href="https://gitlab.kazan.myworldline.com/kazan-community/gitlab-ci-templates/-/tree/master/flavors/terraform" target="_blank">kazan-community/gitlab-ci-templates/-/tree/master/flavors/terraform</a>