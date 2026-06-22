terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
  backend "s3" {
    bucket         = "fiscalai-terraform-state"
    key            = "fiscalai/terraform.tfstate"
    region         = "eu-west-3"
    encrypt        = true
    dynamodb_table = "fiscalai-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "FiscalAI"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

variable "aws_region"   { default = "eu-west-3" }
variable "environment"  { default = "staging" }
variable "db_password"  { sensitive = true }
variable "redis_password" { sensitive = true }
variable "secret_key"   { sensitive = true }

# ── VPC ───────────────────────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.15.0"

  name = "fiscalai-vpc-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["eu-west-3a", "eu-west-3b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true   # cost optimization for staging
  enable_dns_hostnames = true
}

# ── RDS PostgreSQL + PostGIS ──────────────────────────────────────────────────
resource "aws_db_subnet_group" "main" {
  name       = "fiscalai-db-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "rds" {
  name   = "fiscalai-rds-${var.environment}"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}

resource "aws_db_instance" "postgres" {
  identifier              = "fiscalai-${var.environment}"
  engine                  = "postgres"
  engine_version          = "16.4"
  instance_class          = "db.t3.medium"
  allocated_storage       = 100
  storage_type            = "gp3"
  storage_encrypted       = true
  db_name                 = "fiscalai"
  username                = "fiscalai"
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  multi_az                = var.environment == "production"
  backup_retention_period = 7
  deletion_protection     = var.environment == "production"
  skip_final_snapshot     = var.environment != "production"

  # PostGIS is enabled via init SQL script, not via parameter group
}

# ── ElastiCache Redis ─────────────────────────────────────────────────────────
resource "aws_elasticache_subnet_group" "main" {
  name       = "fiscalai-cache-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "redis" {
  name   = "fiscalai-redis-${var.environment}"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "fiscalai-${var.environment}"
  engine               = "redis"
  node_type            = "cache.r6g.medium"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}

# ── ECS Cluster ───────────────────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "fiscalai-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_security_group" "ecs_tasks" {
  name   = "fiscalai-ecs-${var.environment}"
  vpc_id = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── Secrets Manager ───────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "fiscalai/${var.environment}/app"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    DATABASE_URL  = "postgresql://fiscalai:${var.db_password}@${aws_db_instance.postgres.address}:5432/fiscalai"
    REDIS_URL     = "redis://:${var.redis_password}@${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"
    SECRET_KEY    = var.secret_key
  })
}

# ── S3 for documents ──────────────────────────────────────────────────────────
resource "aws_s3_bucket" "documents" {
  bucket = "fiscalai-documents-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_caller_identity" "current" {}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "db_endpoint"    { value = aws_db_instance.postgres.address }
output "redis_endpoint" { value = aws_elasticache_cluster.redis.cache_nodes[0].address }
output "ecs_cluster"    { value = aws_ecs_cluster.main.name }
