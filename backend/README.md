# OrphanAtlas Backend API

Flask-based REST API for rare disease data.

## Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export OPENROUTER_API_KEY="your-key-here"

# Run server
python app.py
```

Server will run on http://localhost:8080

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /api/diseases` - Get all diseases
- `GET /api/search/<query>` - Search disease
- `POST /fetch_data` - Fetch sheet data
- `GET /get_diseases?type=<type>` - Get diseases by type
- `GET /get_disease_count` - Get disease count
- `POST /ask_bot` - Chatbot endpoint
- `POST /get_geographic_spread` - Geographic data
- `GET /download/<query>` - Download PDF report

## Deploy to GCP Cloud Run

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Deploy
gcloud run deploy orphanatlas-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 300 \
  --memory 1Gi \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars OPENROUTER_API_KEY=your-key-here

# Get service URL
gcloud run services describe orphanatlas-api --region us-central1 --format 'value(status.url)'
```

## Environment Variables

- `OPENROUTER_API_KEY` - Required for AI features
- `PORT` - Server port (default: 8080)
