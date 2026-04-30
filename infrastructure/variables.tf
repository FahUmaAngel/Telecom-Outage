variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "telecom-outage"
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}
