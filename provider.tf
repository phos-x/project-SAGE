terraform {
  required_version = ">= 1.5.0"

  backend "http" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1" # Update this if your AWS account is in a different region

  default_tags {
    tags = {
      Platform  = "Project-SAGE"
      ManagedBy = "Terraform-GitOps"
    }
  }
}