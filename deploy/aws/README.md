# AWS deployment (optional, ECS/Fargate primary)

This project is local-first. AWS is not required for tests, simulation, or synthetic workloads. The selected deployment target is **Amazon ECS/Fargate** because it runs the existing Docker image without managing EC2 hosts.

## Architecture

```text
S3 (optional datasets/results)
        ↓
ECS/Fargate FastAPI + Streamlit containers
        ↓
DPSO-GA automation pipeline
        ↓
ECS service desired count (dry-run by default)
        ↓
CloudWatch logs and custom metrics
```

## Required environment variables

```text
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket
AWS_ECS_CLUSTER=dpsoga-cluster
AWS_ECS_SERVICE=dpsoga-backend
AWS_DRY_RUN=true
CLOUDWATCH_NAMESPACE=DPSOGA/Application
```

Use IAM roles/task roles rather than access keys. Never put AWS credentials in source code, Dockerfiles, `.env.example`, or task definitions.

## Install AWS support

Local simulation does not install the AWS SDK. For an AWS-enabled image:

```bash
docker build --build-arg INSTALL_AWS=1 -t dpsoga:aws .
```

Or locally:

```bash
pip install -r requirements-aws.txt
```

## Minimal ECS flow

1. Create an ECR repository and push the Docker image.
2. Create an ECS cluster using Fargate.
3. Create a task definition from `deploy/aws/ecs-task-definition.template.json`.
4. Replace the image URI and secret-free environment values.
5. Attach an execution role with ECR pull and CloudWatch Logs permissions.
6. Attach a task role with only the permissions needed by the enabled features.
7. Create an ECS service with a small desired count such as 1.
8. Keep `AWS_DRY_RUN=true` for the first demonstration.
9. Set `AWS_DRY_RUN=false` only after reviewing the IAM policy, capacity limits, and cooldown controls.

Example ECR commands:

```bash
aws ecr create-repository --repository-name dpsoga --region "$AWS_REGION"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
docker build --build-arg INSTALL_AWS=1 -t dpsoga .
docker tag dpsoga:latest ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/dpsoga:latest
docker push ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/dpsoga:latest
```

These commands do not provision ECS automatically. Review every resource and cost before creation.

## IAM permissions

The minimum conceptual permissions are in `iam-policy.example.json`. Scope resources to the specific bucket, cluster, and service. Typical permissions are:

- S3: `GetObject`, `PutObject`, and `ListBucket` for the workload/results prefixes.
- ECS: `DescribeServices`; `UpdateService` only when real scaling is intentionally enabled.
- CloudWatch: `PutMetricData` and read permissions only if metric queries are enabled.
- CloudWatch Logs: task execution role permissions for log delivery.

## Dry-run and rollback

Dry-run scaling is the default and never changes infrastructure:

```bash
AWS_DRY_RUN=true
```

The API returns a decision such as `SCALE OUT`, `SCALE IN`, or `MAINTAIN` and explicitly labels the result as dry-run. No successful AWS action is claimed in this mode.

For rollback:

```bash
aws ecs update-service --cluster "$AWS_ECS_CLUSTER" --service "$AWS_ECS_SERVICE" --desired-count PREVIOUS_COUNT
```

After a demonstration, delete the ECS service, task definition revisions, ECR images, S3 objects, CloudWatch log groups, and any load balancer that was created. Use the AWS console or reviewed CLI commands; this repository does not auto-delete infrastructure.

## CloudWatch

`CloudWatchMonitor` can publish application metrics such as workload intensity, predicted demand, fitness, and scaling decisions. Configure a namespace with `CLOUDWATCH_NAMESPACE`. Real metric queries and alarms require dimensions matching the deployed ECS service and should be created deliberately to avoid unnecessary cost.
