# Interview prep - ScoutCloud talking points

## One-line pitch

"ScoutCloud is a real-time NBA intelligence platform I built on AWS to
practice everything in the SAA and SAP certifications. It started as a
single EC2 instance with placeholder data and grew into a
Well-Architected, multi-service platform serving 15,000 monthly users."

## The story arc (one chapter per AWS pillar)

1. **EC2 + systemd** - first deploy. user_data clones the repo, gunicorn
   serves the dashboard. Placeholder players, placeholder scores.
2. **EBS snapshots** - reliability. Snapshot the volume daily.
3. **ALB + ASG + Route53 + ACM** - operational excellence. Real domain
   (scoutcloud.dev), HTTPS, multi-AZ.
4. **S3 + GitHub Actions OIDC** - CI/CD. Static assets pushed on every
   merge to main.
5. **RDS PostgreSQL + DynamoDB** - persistence. Players come from
   relational, live scores from NoSQL.
6. **ECS Fargate + Lambda** - serverless compute. Same Docker image as
   EC2, no patching.
7. **CloudFront + edge caching** - performance.
8. **SNS + SQS + DLQ** - decoupling. Score updates fan out to alerts.
9. **CloudWatch + Prometheus + Grafana** - observability.
10. **Custom VPC, three-tier subnets** - networking.
11. **Secrets Manager + KMS + WAF + GuardDuty + Vault** - security.
12. **Rekognition + Comprehend** - AI/ML.
13. **Cost tags + Budgets + cleanup Lambda** - cost optimization.
14. **Cognito + EKS demo** - identity and orchestration.
15. **AWS Backup + Ansible + FIS** - reliability and chaos.

## Frequently asked questions

### "How did you handle secrets?"

Database password lives in Secrets Manager, encrypted with a
customer-managed KMS key. The ECS task role has a tightly scoped
`secretsmanager:GetSecretValue` policy that names the secret ARN
explicitly - no wildcards. At startup, the app calls
`get_secret_value`, extracts the password, and reconstructs
`DATABASE_URL` in memory. The password never appears in an env var,
container definition, or CloudWatch log.

### "How did you control cost?"

Three layers:

1. **Right-sizing** - t2.micro for the dev EC2, db.t3.micro for RDS,
   PAY_PER_REQUEST DynamoDB, 256/512 CPU/memory Fargate task.
2. **Budgets and alarms** - a $60/month budget with email alarms at 80%
   and 100%.
3. **Cleanup automation** - a Lambda runs every Sunday and terminates
   anything tagged `Environment=dev` that has not been touched in 7 days.

### "How would you scale this for the regular season?"

The dev environment is intentionally a single t2.micro and a single
Fargate task. To go to production:

- Switch the ALB target from a single EC2 to an ASG (min 2, max 6).
- Move ECS service to 2+ tasks, behind an ALB target group, autoscaled on
  CPU.
- Switch RDS to a Multi-AZ db.t3.small with a read replica.
- Switch DynamoDB to a provisioned-capacity table with autoscaling.
- Add a CloudFront distribution in front of the ALB and S3 origin.

That is roughly the Chapter 10 to Chapter 13 progression.

### "What would you do differently next time?"

- Start with the VPC and IAM chapters first - I rebuilt the SG twice
  because I added them after EC2 instead of before.
- Use a remote Terraform backend (S3 + DynamoDB lock) from day one
  instead of switching mid-bootcamp.
- Write the Ansible playbook earlier - it would have replaced the
  user_data bash script in Chapter 3.
