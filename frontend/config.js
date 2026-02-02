// API Configuration
// Replace this URL with your GCP Cloud Run URL after deployment
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8080'  // Local development
    : 'https://orphanatlas-api-xxxxx.run.app';  // ← REPLACE WITH YOUR GCP URL

// For production, you can also use environment variable if using build tools:
// const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://orphanatlas-api-xxxxx.run.app';

console.log('API URL:', API_URL);
