import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    api_host: str = os.getenv('API_HOST', '0.0.0.0')
    api_port: int = int(os.getenv('API_PORT', '8000'))
    dashboard_api_url: str = os.getenv('DASHBOARD_API_URL', 'http://localhost:8000')
    dataset_path: str = os.getenv('DATASET_PATH', '')
    results_path: str = os.getenv('RESULTS_PATH', 'results')
    random_seed: int = int(os.getenv('RANDOM_SEED', '42'))
    execution_mode: str = os.getenv('EXECUTION_MODE', 'simulation')
    aws_region: str = os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', ''))
    aws_s3_bucket: str = os.getenv('AWS_S3_BUCKET', '')
    aws_ecs_cluster: str = os.getenv('AWS_ECS_CLUSTER', '')
    aws_ecs_service: str = os.getenv('AWS_ECS_SERVICE', '')
    aws_dry_run: bool = os.getenv('AWS_DRY_RUN', 'true').lower() == 'true'
    min_capacity: int = int(os.getenv('MIN_CAPACITY', '1'))
    max_capacity: int = int(os.getenv('MAX_CAPACITY', '20'))
    safe_utilization: float = float(os.getenv('SAFE_UTILIZATION', '0.75'))
    cooldown_seconds: int = int(os.getenv('COOLDOWN_SECONDS', '0'))
    autoscaling_enabled: bool = os.getenv('AUTOSCALING_ENABLED', 'false').lower() == 'true'
    autoscaling_interval: int = int(os.getenv('AUTOSCALING_INTERVAL', '10'))
    cloudwatch_namespace: str = os.getenv('CLOUDWATCH_NAMESPACE', 'DPSOGA/Application')
    
    db_host: str = os.getenv('DB_HOST', 'localhost')
    db_port: int = int(os.getenv('DB_PORT', '5432'))
    db_name: str = os.getenv('DB_NAME', 'dpsoga')
    db_user: str = os.getenv('DB_USER', 'postgres')
    db_password: str = os.getenv('DB_PASSWORD', 'postgres')

settings = Settings()
