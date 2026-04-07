#!/bin/bash
# Stop RDS for the night — saves ~$0.38/day (~$12/month).
# Lambdas, API GW, SQS cost nothing when idle — no need to touch them.
# RDS can be stopped for up to 7 days; after that AWS auto-starts it.

set -e

DB_INSTANCE="tracktheticket-prod"
REGION="us-east-1"

echo "Stopping RDS instance: $DB_INSTANCE ..."
aws rds stop-db-instance \
  --db-instance-identifier "$DB_INSTANCE" \
  --region "$REGION" \
  --output text --query 'DBInstance.DBInstanceStatus'

echo ""
echo "RDS is stopping (takes ~1-2 min)."
echo "Savings: ~\$0.38/day while stopped."
echo "To start again tomorrow: ./scripts/dev-start.sh"
