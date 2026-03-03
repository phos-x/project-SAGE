module "fraud_detection_workspace" {
  source       = "./modules/ml_workspace"
  project_name = "fraud-detector-v1"
  environment  = "dev"
}

module "churn_prediction_workspace" {
  source       = "./modules/ml_workspace"
  project_name = "customer-churn"
  environment  = "prod"
}