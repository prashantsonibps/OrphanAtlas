#!/bin/bash

# OrphanAtlas Backend - GCP Cloud Run Deployment Script

echo "🚀 Deploying OrphanAtlas Backend to GCP Cloud Run..."
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if OPENROUTER_API_KEY is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OPENROUTER_API_KEY environment variable is not set."
    echo "   AI features will be disabled."
    echo ""
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get project ID
echo "📋 Select your GCP project:"
PROJECT_ID=$(gcloud config get-value project)
echo "   Current project: $PROJECT_ID"
read -p "Use this project? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

# Set variables
SERVICE_NAME="orphanatlas-api"
REGION="us-central1"
MEMORY="1Gi"
TIMEOUT="300"
MIN_INSTANCES="1"
MAX_INSTANCES="10"

echo ""
echo "📦 Deployment Configuration:"
echo "   Service Name: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Memory: $MEMORY"
echo "   Timeout: $TIMEOUT seconds"
echo "   Min Instances: $MIN_INSTANCES"
echo "   Max Instances: $MAX_INSTANCES"
echo ""

read -p "Proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Deploy
echo ""
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --timeout $TIMEOUT \
  --memory $MEMORY \
  --min-instances $MIN_INSTANCES \
  --max-instances $MAX_INSTANCES \
  --set-env-vars OPENROUTER_API_KEY="$OPENROUTER_API_KEY"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Getting service URL..."
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    echo ""
    echo "✨ Your API is live at:"
    echo "   $SERVICE_URL"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Copy the URL above"
    echo "   2. Update frontend/config.js with this URL"
    echo "   3. Deploy the frontend to Vercel"
    echo ""
else
    echo ""
    echo "❌ Deployment failed. Please check the error messages above."
    exit 1
fi
