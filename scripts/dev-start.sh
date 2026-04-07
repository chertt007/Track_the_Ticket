#!/bin/bash
# Start RDS in the morning and wait until it's ready to accept connections.

set -e

DB_INSTANCE="tracktheticket-prod"
REGION="us-east-1"

echo "Starting RDS instance: $DB_INSTANCE ..."
aws rds start-db-instance \
  --db-instance-identifier "$DB_INSTANCE" \
  --region "$REGION" \
  --output text --query 'DBInstance.DBInstanceStatus'

echo ""
echo "Waiting for RDS to become available (usually 2-3 min)..."
aws rds wait db-instance-available \
  --db-instance-identifier "$DB_INSTANCE" \
  --region "$REGION"

echo ""
echo "RDS is ready!"
