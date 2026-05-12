# ADR-002: AWS region selection

**Status:** Accepted
**Date:** 2026-05-11
**Deciders:** Marcus Diaz (Lead Engineer), Diana Chen (CTO, ScoutCloud)

## Context

ScoutCloud will run on AWS (see [ADR-001](./ADR-001-cloud-provider.md)).
We must choose one primary AWS region. The region influences:

- Latency from end users (predominantly East Coast - NBA HQ is in
  Manhattan, our pilot front-office customer is the Knicks).
- Service availability (some AWS services launch in us-east-1 first).
- Cost (us-east-1 is the cheapest US region for almost every service).
- Disaster-recovery posture (Chapter 18 will introduce a DR region).

We evaluated four candidates: us-east-1, us-east-2, us-west-2, and
ca-central-1.

## Decision

We will use **us-east-1 (N. Virginia)** as the primary AWS region for
all infrastructure deployed during the bootcamp.

## Options considered

### Option A - us-east-1 (chosen)

- Lowest latency to the New York metro area (~10-15 ms).
- Every AWS service we will use is GA here, often launched here first
  (Bedrock, Rekognition Custom Labels, GuardDuty Malware Protection).
- Cheapest pricing tier for EC2, RDS, and Fargate among US regions.
- ACM certificates for CloudFront must live in us-east-1 - using us-east-1
  for the rest of the stack removes a cross-region ACM dance.

### Option B - us-east-2 (Ohio)

- ~5 ms higher latency to NY than us-east-1.
- Slightly cheaper egress to North American customers but our total egress
  is <50 GB/month - the savings are <$1.
- Newer services lag by 1-3 months on average.

### Option C - us-west-2 (Oregon)

- ~70 ms latency to NY - unacceptable for the live-score 30 s SLO once
  the round-trip through CDN, ALB, and DDB scan is included.
- Cheaper renewable energy mix - a nice-to-have but not a deciding factor.

### Option D - ca-central-1 (Montreal)

- Data-residency benefit for Canadian fans but the league office is in NY
  and our pilot front-office customer is in NY.
- Smaller AZ count (3 vs 6 in us-east-1) reduces multi-AZ flexibility.

## Consequences

**Positive**

- One region for ACM, ALB, ECS, RDS, DynamoDB, Lambda, Cognito - no
  cross-region permission grants needed.
- Faster access to new AI/ML capabilities as they roll out (relevant for
  Chapter 15).

**Negative**

- us-east-1 has a documented history of larger blast-radius outages
  (Dec 2021, Jun 2023). Mitigated in Chapter 18 by adding AWS Backup
  cross-region copies to us-east-2.
- Front-office customers in EU or APAC would see higher latency. Mitigated
  by serving static assets through CloudFront's global edge network
  (Chapter 10).

## References

- [AWS Regional Services List](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/)
- [ADR-001: Cloud provider selection](./ADR-001-cloud-provider.md)
