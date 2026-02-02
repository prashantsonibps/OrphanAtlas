#!/bin/bash

# OrphanAtlas Backend - FREE TIER Deployment
# NO MIN-INSTANCES = NO MONTHLY COSTS!

echo "🆓 Deploying OrphanAtlas Backend (100% FREE TIER)"
echo "⚠️  Note: First load will have 5-10s cold start (normal for free tier)"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
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

# Enable Cloud Run API if not already enabled
echo ""
echo "🔧 Ensuring Cloud Run API is enabled..."
gcloud services enable run.googleapis.com --project=$PROJECT_ID

# Set variables for FREE TIER
SERVICE_NAME="orphanatlas-api"
REGION="us-central1"
MEMORY="512Mi"  # Can increase to 1Gi if needed (still free)
TIMEOUT="300"
MAX_INSTANCES="5"  # Prevents runaway costs

echo ""
echo "💰 FREE TIER Configuration:"
echo "   Service Name: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Memory: $MEMORY (can be increased to 1Gi if needed)"
echo "   Timeout: $TIMEOUT seconds"
echo "   Min Instances: 0 (FREE - accepts cold starts)"
echo "   Max Instances: $MAX_INSTANCES (prevents excess costs)"
echo ""
echo "💡 This deployment is 100% FREE (within GCP free tier limits)"
echo "   - 2 million requests/month"
echo "   - 360,000 GB-seconds memory"
echo "   - 180,000 vCPU-seconds compute"
echo ""

read -p "Proceed with FREE TIER deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Deploy with FREE TIER settings
echo ""
echo "🚀 Deploying to Cloud Run (FREE TIER)..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --timeout $TIMEOUT \
  --memory $MEMORY \
  --cpu 1 \
  --max-instances $MAX_INSTANCES \
  --no-cpu-throttling=false \
  --set-env-vars OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"

# Note: NO --min-instances flag = FREE!

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful (FREE TIER)!"
    echo ""
    echo "🌐 Getting service URL..."
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    echo ""
    echo "✨ Your API is live at:"
    echo "   $SERVICE_URL"
    echo ""
    echo "⚠️  IMPORTANT: Free Tier Notes"
    echo "   1. First load: 5-10 second cold start (normal)"
    echo "   2. After cold start: Fast response (<2s)"
    echo "   3. Idle for 15 min: Goes to sleep, cold start again"
    echo "   4. This is FREE - no monthly charges!"
    echo ""
    echo "💰 Cost Monitoring:"
    echo "   - Set up budget alerts: https://console.cloud.google.com/billing/budgets"
    echo "   - Current usage: https://console.cloud.google.com/billing"
    echo "   - Expected cost: \$0/month (within free tier)"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Copy the URL above"
    echo "   2. Update frontend/config.js with this URL"
    echo "   3. Deploy the frontend to Vercel (also FREE)"
    echo ""
else
    echo ""
    echo "❌ Deployment failed. Please check the error messages above."
    exit 1
fi
