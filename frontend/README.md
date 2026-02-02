# OrphanAtlas Frontend

Static HTML frontend for the OrphanAtlas rare disease database.

## Setup

1. **Update API URL** in `config.js`:
   ```javascript
   const API_URL = 'https://your-backend-url.run.app';
   ```

2. **Test locally**:
   ```bash
   # Use any static server
   python3 -m http.server 3000
   # or
   npx serve .
   ```

3. **Deploy to Vercel**:
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Login
   vercel login
   
   # Deploy
   vercel --prod
   ```

## File Structure

```
frontend/
├── index.html          # Homepage
├── blocks.html         # Disease results page
├── config.js           # API configuration
├── static/             # Images and assets
│   ├── logo.png
│   ├── female_lab_scientist.png
│   └── ...
├── vercel.json         # Vercel configuration
└── README.md
```

## Features

- ✅ Disease search with autocomplete
- ✅ Browse diseases alphabetically or by prevalence
- ✅ View disease data across multiple categories
- ✅ AI-powered chatbot
- ✅ Download PDF reports
- ✅ Responsive mobile design

## Environment

This is a pure static site - no build process required. All API calls are made client-side to the backend hosted on GCP.

## Deployment

### Option 1: Vercel (Recommended)
```bash
vercel --prod
```

### Option 2: Netlify
```bash
netlify deploy --prod --dir=.
```

### Option 3: GitHub Pages
```bash
# Push to gh-pages branch
git subtree push --prefix frontend origin gh-pages
```

## Configuration

After deployment, make sure:
1. Backend CORS is configured to allow your Vercel domain
2. API_URL in config.js points to your GCP backend
3. Test all features work correctly

## Performance

- Images are served via Vercel's CDN
- Static HTML loads in < 1 second
- API calls to GCP backend are the only network delay
- Aggressive caching for static assets

## Troubleshooting

**Issue: "Failed to fetch" errors**
- Check that API_URL in config.js is correct
- Verify backend is running and accessible
- Check browser console for CORS errors

**Issue: Images not loading**
- Verify paths in HTML use `static/` not `/static/`
- Check all images exist in static/ folder

**Issue: Search not working**
- Open browser DevTools and check Network tab
- Verify API endpoints are responding
- Check for JavaScript errors in Console
