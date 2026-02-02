# OrphanAtlas

A comprehensive rare disease database with AI-powered insights, covering over 4000 rare diseases.

## Features

- **Disease Search**: Search and explore 4000+ rare diseases with detailed information
- **AI Chatbot**: Ask questions about rare diseases and get instant answers
- **Geographic Spread**: Visualize where diseases are most prevalent globally
- **PDF Reports**: Download comprehensive disease reports
- **Data Categories**: Prevalence, Publications, Classification, Symptoms, Inheritance, Genetic Variation, Treatments, and Biopharma Pipeline

## Architecture

- **Frontend**: Static HTML/CSS/JS hosted on Vercel
- **Backend**: Flask API hosted on GCP Cloud Run
- **AI**: DeepSeek V3 via OpenRouter API

## Tech Stack

**Backend:**
- Flask (Python web framework)
- Pandas (Data processing)
- FPDF (PDF generation)
- OpenAI (AI integration)

**Frontend:**
- HTML/CSS/JavaScript
- Leaflet.js (Maps)
- Particles.js (Effects)

## Data Sources

- Orphanet (Rare disease database)
- FDA (Drug approvals)
- PubMed (Research publications)

## Local Development

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENROUTER_API_KEY="your-api-key"
python app.py
```

**Frontend:**
```bash
cd frontend
python3 -m http.server 3000
```

Visit `http://localhost:3000`

## Deployment

- Frontend: Deploy `frontend/` folder to Vercel
- Backend: Deploy `backend/` folder to GCP Cloud Run

Set `OPENROUTER_API_KEY` environment variable in GCP Cloud Run for AI features.

## License

Educational and research purposes.
