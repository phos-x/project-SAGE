variable "project_name" {
  type        = string
  description = "Name of the ML project requested via the IDP"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment (dev, stg, prod)"
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform-GitOps-Platform"
  }
}
