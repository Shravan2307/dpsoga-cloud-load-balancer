variable "aws_region" {
  description = "AWS region for deployments (Free-tier eligible)"
  type        = string
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Base name for resources"
  type        = string
  default     = "dpsoga"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_user" {
  description = "Database master username"
  type        = string
  default     = "dpsoga_admin"
}

