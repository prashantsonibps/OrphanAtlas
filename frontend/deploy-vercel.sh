#!/bin/bash

# OrphanAtlas Frontend - Vercel Deployment Script

echo "🚀 Deploying OrphanAtlas Frontend to Vercel..."
echo ""

# Check if vercel is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed. Installing now..."
    npm install -g vercel
fi

# Check if config.js has been updated
if grep -q "orphanatlas-api-xxxxx.run.app" config.js; then
    echo "⚠️  Warning: config.js still contains placeholder API URL!"
    echo "   Please update the API_URL in config.js with your GCP Cloud Run URL."
    echo ""
    read -p "Have you updated config.js with your backend URL? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "📝 Please update config.js first:"
        echo "   const API_URL = 'https://your-actual-backend-url.run.app';"
        echo ""
        exit 1
    fi
fi

echo ""
echo "📦 Deployment Configuration:"
echo "   Platform: Vercel"
echo "   Project: orphanatlas-frontend"
echo ""

read -p "Proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Deploy
echo ""
echo "🚀 Deploying to Vercel..."
vercel --prod

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Test your frontend at the URL shown above"
    echo "   2. Verify search functionality works"
    echo "   3. Test the chatbot and AI features"
    echo "   4. Check that all images load correctly"
    echo ""
else
    echo ""
    echo "❌ Deployment failed. Please check the error messages above."
    exit 1
fi
