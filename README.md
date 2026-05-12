# ScoutCloud - NBA Intelligence Platform

[![Deploy Static Assets](https://github.com/NetXav/scoutcloud.dev/actions/workflows/deploy-static.yml/badge.svg)](https://github.com/NetXav/scoutcloud.dev/actions/workflows/deploy-static.yml)
[![Build and Push Docker Image](https://github.com/NetXav/scoutcloud.dev/actions/workflows/build-push-image.yml/badge.svg)](https://github.com/NetXav/scoutcloud.dev/actions/workflows/build-push-image.yml)

> Live at **[scoutcloud.dev](https://scoutcloud.dev)**

A production-grade real-time NBA intelligence platform built on AWS.
Started as a single EC2 instance with placeholder data.
Evolved into a Well-Architected, multi-service platform serving 15,000 users.

## Architecture

![ScoutCloud Architecture](docs/architecture-diagram.png)

## What it does

**For fans - free tier (scoutcloud.dev)**
- Live game scores updated every 5 minutes via Lambda + DynamoDB
- Player statistics from PostgreSQL on RDS
- Player photos automatically tagged using Amazon Rekognition AI

**For NBA front offices - $499/month**
- Shot charts by defensive matchup and zone
- 30+ real-time alert types via SNS notifications
- Fan sentiment analysis using Amazon Comprehend
- Authenticated API access via Amazon Cognito JWT tokens

## Technology stack

| Layer | Technologies |
|---|---|
| Compute | EC2 Auto Scaling Group, ECS Fargate, AWS Lambda |
| Database | RDS PostgreSQL, Amazon DynamoDB |
| Storage | Amazon S3, Amazon EBS |
| CDN | Amazon CloudFront, Route53 |
| Security | WAF, GuardDuty, KMS, Secrets Manager, HashiCorp Vault |
| CI/CD | GitHub Actions (OIDC), GitLab CI, AWS CodePipeline |
| IaC | Terraform (modules, remote state, S3 + DynamoDB backend) |
| Monitoring | CloudWatch, Prometheus, Grafana |
| AI/ML | Amazon Rekognition, Amazon Comprehend |
| Orchestration | Amazon EKS (Kubernetes) |
| Configuration | Ansible |
| Auth | Amazon Cognito |

## Quick start (local)

```bash
git clone https://github.com/YOUR-USERNAME/scoutcloud.dev.git ~/scoutcloud
cd ~/scoutcloud
make run
# open http://localhost:8080
```

## Deploy to AWS

```bash
make init     # terraform init
make plan     # terraform plan
make apply    # terraform apply
```

Prerequisites: AWS CLI configured, Terraform >= 1.5.0, Docker running.

## AWS Cost (dev environment)

| Service | Monthly cost |
|---|---|
| EC2 2x t2.micro (ASG) | $17 |
| RDS db.t3.micro | $15 |
| Application Load Balancer | $16 |
| CloudFront (10 GB) | $1 |
| Lambda (1M invocations) | $0.20 |
| DynamoDB (PAY_PER_REQUEST) | $2 |
| **Total** | **~$51** |

## Well-Architected review

Last reviewed: 2026-05-11. Zero HIGH RISK findings.
See [docs/well-architected-report.pdf](docs/well-architected-report.pdf)

## Key engineering decisions

- [ADR-001: Cloud provider selection](docs/ADR-001-cloud-provider.md)
- [ADR-002: Region selection](docs/ADR-002-region-selection.md)
- [Interview prep](docs/interview-prep.md)
