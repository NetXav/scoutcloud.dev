# ADR-001: Cloud provider selection

**Status:** Accepted
**Date:** 2026-05-11
**Deciders:** Marcus Diaz (Lead Engineer), Diana Chen (CTO, ScoutCloud)

## Context

ScoutCloud is a B2C/B2B real-time NBA intelligence platform with two
tiers:

- **Free tier** at scoutcloud.dev - live scores, player stats, ~15,000 monthly
  active users.
- **Front-office tier** at $499/month - shot charts by defensive matchup, 30+
  real-time alerts, fan sentiment analysis, AI photo tagging.

The platform must serve scores within 30 seconds of live updates, provide
99.9% availability during the regular season, and pass the league's
information-security review before signing the first front-office contract.

We evaluated three cloud providers: AWS, Google Cloud, and Azure.

## Decision

We will use **Amazon Web Services (AWS)** as the primary cloud provider.

## Options considered

### Option A - AWS (chosen)

- Largest managed-service breadth: ECS Fargate, Lambda, RDS, DynamoDB,
  Cognito, Rekognition, Comprehend all integrate natively.
- Strong IaC ecosystem: Terraform AWS provider has first-class support for
  every service we need.
- OIDC for GitHub Actions removes the need to mint long-lived access keys
  in CI/CD.
- Cost-controls are mature: budget alarms, cost-allocation tags, S3
  Intelligent-Tiering.
- The lead engineer holds AWS SAA and is studying SAP - team knowledge
  matches the platform.

### Option B - Google Cloud

- Strong on Kubernetes (GKE Autopilot) and BigQuery, but our analytics
  volume is small (~50 GB) and BigQuery is overkill.
- Vertex AI is excellent but we already chose Rekognition for photo tagging
  and Comprehend for sentiment, both of which beat Vertex on price for our
  volume.
- Fewer engineers on the team have GCP experience.

### Option C - Azure

- Strong identity story (Entra ID) but we are not an enterprise customer,
  so the discount structure does not apply.
- Azure Cognitive Services pricing is higher than the AWS AI equivalents at
  our scale.
- Smaller community for Terraform modules.

## Consequences

**Positive**

- Single bill, single IAM model, single audit log.
- All bootcamp chapters map cleanly to AWS services - no awkward
  cross-cloud translation.
- HSTS-preloaded `.dev` TLD on Route53 forces HTTPS without extra config.

**Negative**

- Vendor lock-in. Mitigated by using Terraform for everything and keeping
  the application Docker-portable (Chapter 8 proves the same image runs on
  ECS and EKS).
- AWS bill must stay under $60/month for the dev environment. Mitigated
  with budget alarms (Chapter 16) and PAY_PER_REQUEST DynamoDB.

## References

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [ADR-002: Region selection](./ADR-002-region-selection.md)
