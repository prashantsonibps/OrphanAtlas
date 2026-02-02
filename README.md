# OrphanAtlas

> Rare disease database with AI-powered insights. 4000+ diseases, searchable, with chatbot and PDF reports.

## 🚀 Quick Deploy (100% FREE)

```bash
# 1. Deploy Backend to GCP Cloud Run
cd backend
export OPENROUTER_API_KEY="your-key-optional"
./deploy-free-tier.sh

# 2. Update frontend/config.js with your backend URL

# 3. Deploy Frontend to Vercel
cd frontend
vercel --prod
```

**Cost: $0/month** (within free tier)

---

## 🏗️ Architecture

- **Backend**: Flask API on GCP Cloud Run (FREE tier, accepts cold starts)
- **Frontend**: Static HTML on Vercel (FREE forever)
- **AI**: DeepSeek V3 via OpenRouter (pay-as-you-go, ~$0-5/month)

---

## ✨ Features

- Search 4000+ rare diseases
- AI chatbot for questions
- Geographic spread visualization
- Download PDF reports
- Mobile responsive

---

## 📊 Data Categories

1. Prevalence
2. Publications
3. Classification
4. Symptoms
5. Inheritance
6. Genetic Variation
7. Approved Treatments
8. Biopharma Pipeline

---

## 🛠️ Local Development

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Frontend:**
```bash
cd frontend
python3 -m http.server 3000
```

---

## ⚙️ Tech Stack

- **Backend**: Flask, Pandas, FPDF, OpenAI
- **Frontend**: HTML/CSS/JS, Leaflet, Particles.js
- **Hosting**: GCP Cloud Run, Vercel

---

## 💰 Free Tier Notes

- First load: 5-10s (backend cold start - normal for free tier)
- Subsequent loads: <2s (backend stays awake)
- **Set budget alerts**: https://console.cloud.google.com/billing/budgets

---

## 📝 Credits

Data: Orphanet, FDA, PubMed  
AI: DeepSeek V3  
Hosting: GCP, Vercel
