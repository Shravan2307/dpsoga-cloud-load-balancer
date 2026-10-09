from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

class SimulationAdapter:
    mode = 'simulation'
    def status(self):
        return {'mode': self.mode, 'status': 'available', 'provider': 'local-simulator'}
    def metrics(self):
        return {'mode': self.mode, 'metrics': {}, 'message': 'Use workload analysis and simulator results for local metrics.'}
    def scale(self, desired_capacity: int, dry_run: bool = True):
        return {'mode': self.mode, 'dry_run': dry_run, 'status': 'simulated', 'desired_capacity': desired_capacity}

class AWSCloudAdapter:
    mode = 'aws'
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.cluster = os.getenv('AWS_ECS_CLUSTER', '')
        self.service = os.getenv('AWS_ECS_SERVICE', '')
        self.region = os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', ''))
        self._ecs = None
        self._cloudwatch = None
    def _clients(self):
        if self._ecs is None:
            try:
                import boto3
            except ImportError as exc:
                raise RuntimeError('AWS mode requires boto3; install requirements-aws.txt or enable the AWS extra.') from exc
            self._ecs = boto3.client('ecs', region_name=self.region or None)
            self._cloudwatch = boto3.client('cloudwatch', region_name=self.region or None)
        return self._ecs, self._cloudwatch
    def status(self):
        if self.dry_run:
            return {'mode': self.mode, 'status': 'dry-run', 'cluster': self.cluster, 'service': self.service, 'region': self.region}
        if not self.cluster or not self.service:
            raise RuntimeError('AWS_ECS_CLUSTER and AWS_ECS_SERVICE are required for AWS mode.')
        ecs, _ = self._clients()
        data = ecs.describe_services(cluster=self.cluster, services=[self.service])
        services = data.get('services', [])
        if not services:
            raise RuntimeError('Configured ECS service was not found.')
        s = services[0]
        return {'mode': self.mode, 'status': s.get('status'), 'desired_count': s.get('desiredCount'), 'running_count': s.get('runningCount'), 'cluster': self.cluster, 'service': self.service, 'region': self.region}
    def metrics(self):
        return {'mode': self.mode, 'status': 'dry-run' if self.dry_run else 'available', 'metrics': {}, 'message': 'CloudWatch metric queries require configured namespaces and dimensions.'}
    def scale(self, desired_capacity: int, dry_run: bool | None = None):
        effective_dry_run = self.dry_run if dry_run is None else dry_run
        payload = {'mode': self.mode, 'desired_capacity': desired_capacity, 'dry_run': effective_dry_run, 'timestamp': datetime.now(timezone.utc).isoformat()}
        if effective_dry_run:
            payload['status'] = 'dry-run; no AWS infrastructure changed'
            return payload
        if not self.cluster or not self.service:
            raise RuntimeError('AWS_ECS_CLUSTER and AWS_ECS_SERVICE are required for scaling.')
        ecs, _ = self._clients()
        response = ecs.update_service(cluster=self.cluster, service=self.service, desiredCount=int(desired_capacity))
        payload['status'] = 'submitted'
        payload['service'] = response.get('service', {}).get('serviceName', self.service)
        return payload

class S3Store:
    def __init__(self, bucket: str | None = None, prefix: str = '', dry_run: bool | None = None):
        self.bucket = bucket or os.getenv('AWS_S3_BUCKET', '')
        self.prefix = prefix.strip('/')
        self.dry_run = dry_run if dry_run is not None else (os.getenv('AWS_DRY_RUN', 'true').lower() == 'true')
        
    def _client(self):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError('S3 mode requires boto3.') from exc
        if not self.bucket:
            raise RuntimeError('AWS_S3_BUCKET is required for S3 operations.')
        return boto3.client('s3', region_name=os.getenv('AWS_REGION', 'eu-north-1'))

    def upload_bytes(self, key: str, content: bytes, content_type: str = 'text/csv'):
        full_key = f'{self.prefix}/{key}'.strip('/')
        if self.dry_run:
            return {'bucket': self.bucket or 'dry-run-bucket', 'key': full_key, 'status': 'dry-run-uploaded'}
        self._client().put_object(Bucket=self.bucket, Key=full_key, Body=content, ContentType=content_type)
        return {'bucket': self.bucket, 'key': full_key, 'status': 'uploaded'}

    def upload_file(self, file_path: str, key: str | None = None, content_type: str = 'application/octet-stream'):
        if not key:
            import os
            key = os.path.basename(file_path)
        full_key = f'{self.prefix}/{key}'.strip('/')
        if self.dry_run:
            return {'bucket': self.bucket or 'dry-run-bucket', 'key': full_key, 'status': 'dry-run-uploaded'}
        self._client().upload_file(file_path, self.bucket, full_key, ExtraArgs={'ContentType': content_type})
        return {'bucket': self.bucket, 'key': full_key, 'status': 'uploaded'}

    def download_bytes(self, key: str) -> bytes:
        full_key = f'{self.prefix}/{key}'.strip('/')
        if self.dry_run:
            return b"dry-run-content"
        return self._client().get_object(Bucket=self.bucket, Key=full_key)['Body'].read()

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        full_key = f'{self.prefix}/{key}'.strip('/')
        if self.dry_run:
            return f"https://s3.dry-run.amazonaws.com/{self.bucket or 'dry-run-bucket'}/{full_key}?expires={expiration}"
        return self._client().generate_presigned_url('get_object', Params={'Bucket': self.bucket, 'Key': full_key}, ExpiresIn=expiration)

class CloudWatchMonitor:
    def __init__(self, namespace: str = 'DPSOGA/Application'):
        self.namespace = namespace
    def put_metrics(self, metrics: dict[str, float], dry_run: bool = True):
        if dry_run:
            return {'status': 'dry-run', 'namespace': self.namespace, 'metrics': metrics}
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError('CloudWatch mode requires boto3.') from exc
        client = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION') or None)
        data = [{'MetricName': k, 'Value': float(v), 'Unit': 'None'} for k, v in metrics.items()]
        client.put_metric_data(Namespace=self.namespace, MetricData=data)
        return {'status': 'published', 'namespace': self.namespace, 'metrics': metrics}
