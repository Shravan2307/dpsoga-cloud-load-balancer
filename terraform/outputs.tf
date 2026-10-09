output "ec2_public_ip" {
  description = "Public IP of the Application EC2 instance"
  value       = aws_instance.app.public_ip
}

output "s3_bucket_name" {
  description = "Name of the created S3 bucket"
  value       = aws_s3_bucket.artifacts.id
}

output "rds_endpoint" {
  description = "Endpoint for the PostgreSQL RDS instance"
  value       = aws_db_instance.postgres.endpoint
}

