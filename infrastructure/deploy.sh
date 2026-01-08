#!/bin/bash
set -e

echo "🚀 Deploying Pokemon Card Scanner API..."

# Variables
STACK_NAME="pokemon-card-scanner"
REGION="${AWS_REGION:-us-east-1}"
MODEL_VERSION="${1:-v1}"

echo "📦 Building SAM application..."
sam build

echo "🔐 Deploying to AWS..."
sam deploy \
  --stack-name $STACK_NAME \
  --region $REGION \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides ModelVersion=$MODEL_VERSION \
  --no-confirm-changeset

echo "✅ Deployment complete!"
echo ""
echo "📋 Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs' \
  --output table
