# 🌿 Project SAGE: Serverless Automated GitOps Environment

**SAGE** is a zero-touch, self-service MLOps platform designed to reduce the time-to-market for Machine Learning models from weeks to minutes.

By leveraging GitOps principles, modular Terraform, and AWS Serverless infrastructure, SAGE empowers Data Scientists to instantly provision compliant, secure, and highly scalable inference environments without requiring manual IT intervention.

## 🎯 The Problem vs. The SAGE Solution

* **The Problem:** Data Science teams often face significant friction when transitioning models from local Jupyter Notebooks to production REST APIs. Infrastructure provisioning relies on manual IT tickets, leading to configuration drift, security vulnerabilities, and blocked deployments.
* **The SAGE Solution:** A standardized GitOps pipeline. A Data Scientist simply adds their project configuration to the repository. SAGE automatically runs unit tests, scans for CVEs, provisions isolated AWS infrastructure (S3, API Gateway, Lambda/ECR), and wires up a production-ready HTTP endpoint.

## ✨ Core Platform Features

* **Self-Service IaC (Terraform):** Standardized modules ensure every deployed model environment includes FinOps cost-tracking tags, encrypted-at-rest S3 buckets, and least-privilege IAM roles by default.
* **DevSecOps & Shift-Left Security:** Integrated **Trivy** scanning fails the pipeline automatically if `MEDIUM`, `HIGH`, or `CRITICAL` vulnerabilities are detected in the infrastructure or Python dependencies.
* **Cold-Start Optimized Compute:** The serverless inference layer (AWS Lambda via Docker/ECR) uses an object-oriented Python architecture to cache the ML model in memory, reducing warm-start inference latency to milliseconds.
* **Fail-Fast Data Validation:** The API layer rejects malformed JSON or incorrect data types in $O(N)$ time, preventing expensive and unnecessary compute cycles.

## 📂 Repository Structure

```text
project-sage/
├── .gitlab-ci.yml                 # DevSecOps Pipeline (Test, Scan, Plan, Apply)
├── main.tf                        # GitOps Entrypoint (Developer declarations)
├── modules/
│   └── ml_workspace/              # Reusable Terraform module
│       ├── api_gw.tf              # HTTP API Gateway
│       ├── iam.tf                 # Least-privilege execution roles
│       ├── lambda.tf              # Serverless compute (ECR Image mapping)
│       └── s3.tf                  # Model artifact storage
├── src/
│   ├── app.py                     # Optimized model loading & inference logic
│   ├── Dockerfile                 # Custom AWS Lambda container definition
│   └── requirements.txt           # ML dependencies (scikit-learn, joblib, etc.)
└── tests/
    └── test_app.py                # Pytest suite with Boto3/S3 mocking

```

## 🚀 How to Deploy

### Prerequisites

* AWS CLI configured with administrator/provisioning credentials.
* Terraform `v1.5+` installed.
* Docker daemon running.

### Local Deployment (For Testing)

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/project-sage.git
cd project-sage

```


2. **Run the test suite:**
```bash
pytest tests/test_app.py

```


3. **Initialize and Apply Terraform:**
```bash
terraform init
terraform plan
terraform apply -auto-approve

```


4. **Test the live endpoint:**
```bash
curl -X POST $(terraform output -raw api_endpoint)/predict \
-H "Content-Type: application/json" \
-d '{"features": [1.5, 0.5, 3.2]}'

```



## 🧑‍💻 The Developer Workflow (GitOps)

1. **Request:** A Data Scientist submits a Merge Request adding a new module block to `main.tf` (e.g., `module "fraud_detection"`).
2. **Test & Scan:** GitLab CI automatically runs Pytest and Trivy.
3. **Review:** The Platform Team reviews the automated `terraform plan` output generated in the MR.
4. **Merge & Provision:** Upon merging to `main`, the infrastructure is automatically provisioned and the Data Scientist receives their secure S3 bucket and API URL.

## 🛣️ Future Roadmap

* **Kubernetes (EKS) Migration Path:** While SAGE currently uses Lambda/ECR for cost-effective burst traffic, future iterations will include a toggle to deploy heavier workloads (e.g., LLMs requiring GPUs) to an EKS cluster running KServe.
* **Automated Model Retraining:** Integrating AWS EventBridge and Step Functions to trigger automated retraining pipelines when data drift is detected.

---

```mermaid
graph TD
    %% Define Styles
    classDef gitops fill:#e24329,stroke:#fca326,stroke-width:2px,color:#fff;
    classDef terraform fill:#5c4ee5,stroke:#fff,stroke-width:2px,color:#fff;
    classDef cfn fill:#ff9900,stroke:#fff,stroke-width:2px,color:#fff;
    classDef aws fill:#ff9900,stroke:#232f3e,stroke-width:2px,color:#232f3e;
    classDef monitor fill:#d13212,stroke:#fff,stroke-width:2px,color:#fff;

    %% GitOps Pipeline Subgraph
    subgraph "GitOps DevSecOps Pipeline (GitLab CI/CD)"
        Dev([Data Scientist / Engineer]) -->|Push/MR| Code[GitLab Repository]
        Code --> Test[Pytest & Trivy Sec Scan]
        Test --> Lint[TF Validate & CFN Lint]
        Lint --> Plan[TF Plan / CFN ChangeSet]
        Plan --> Merge{Merge to Main?}
        Merge -- Yes --> Deploy[Automated Deployment]
    end

    %% MLOps Stack Subgraph
    subgraph "MLOps Inference Stack (Provisioned by Terraform)"
        API[API Gateway] -->|REST Request| MLLambda[Lambda Inference Container]
        MLLambda <-->|Loads Model & O-1 Caching| MLS3[(S3: ML Models & Data)]
    end

    %% Data Platform Subgraph
    subgraph "Event-Driven Data Platform (Provisioned by CloudFormation)"
        Cron[EventBridge Rules] -->|Trigger| IngestLambda[Lambda Ingestor]
        IngestLambda -->|Writes JSON| RawS3[(S3: Raw Zone)]
        RawS3 -->|Triggers| SF[Step Functions Orchestrator]
        SF -->|Runs| Glue[Glue PySpark ETL Job]
        Glue -->|Saves Parquet| CuratedS3[(S3: Curated Zone)]
    end

    %% Observability Subgraph
    subgraph "Observability & Day 2 Operations"
        IngestLambda -.->|Failure DLQ| SQS[SQS: Dead Letter Queue]
        SF -.->|Catch & Retry Failures| SNS[SNS: Alerting Topic]
        CloudWatch((CloudWatch Alarms)) -.-> SNS
        IngestLambda -.->|Metrics| CloudWatch
    end

    %% Connecting the layers
    Deploy ==>|Deploys| API
    Deploy ==>|Deploys| Cron
    
    %% Apply classes
    class Code,Test,Lint,Plan,Merge,Deploy gitops;
    class API,MLLambda,MLS3 terraform;
    class Cron,IngestLambda,RawS3,SF,Glue,CuratedS3 cfn;
    class SQS,SNS,CloudWatch monitor;
```

*Developed by phos-x for Platform Engineering & MLOps demonstrations.*
