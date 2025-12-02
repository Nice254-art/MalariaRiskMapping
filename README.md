# Malaria Risk Mapping & Prediction

A full-stack geospatial application that predicts malaria risk using real-time satellite data from Google Earth Engine (GEE).

## 🚀 Features
- **Real-time Risk Analysis**: Uses GEE to fetch Rainfall, Temperature, NDVI, and more.
- **Machine Learning**: Predicts risk levels (Low, Medium, High) based on environmental factors.
- **Interactive Map**: Click anywhere on the map to analyze a specific location.
- **API Backend**: Secure FastAPI backend handles Earth Engine authentication and data retrieval.
- **Mobile Responsive**: Optimized for use on all devices.

## 🛠️ Architecture
- **Frontend**: Streamlit (UI, Map, Charts)
- **Backend**: FastAPI (Earth Engine Logic, ML Inference)
- **Database**: SQLite (Local prediction history)

## 📦 Setup & Installation

### Prerequisites
- Python 3.9+
- Google Earth Engine Service Account

### 1. Clone the Repository
```bash
git clone https://github.com/Nice254-art/MalariaRiskMapping.git
cd MalariaRiskMapping
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory (see `.env.example`):
```ini
# Google Earth Engine Credentials
EE_SERVICE_ACCOUNT=your-service-account@your-project.iam.gserviceaccount.com
EE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# Backend URL (for local dev)
API_URL=http://localhost:8000
```

### 4. Run Locally
You need to run both the backend and the frontend.

**Terminal 1 (Backend):**
```bash
uvicorn api:app --reload
```

**Terminal 2 (Frontend):**
```bash
streamlit run app.py
```

## ☁️ Deployment

### Option 1: Render (Recommended)
This repo is configured for Render "Blueprints".
1.  Go to [Render Dashboard](https://dashboard.render.com/).
2.  Click **New +** -> **Blueprint**.
3.  Connect this repository.
4.  Render will automatically detect `render.yaml` and propose two services:
    - `malaria-api`: The backend.
    - `malaria-ui`: The frontend.
5.  **Important**: You must add your `EE_SERVICE_ACCOUNT` and `EE_PRIVATE_KEY` as environment variables in the Render dashboard for the `malaria-api` service.

### Option 2: Streamlit Cloud + External API
1.  Deploy the API (e.g., to Render or Railway) using the `Procfile` or `render.yaml`.
2.  Deploy the Streamlit app to [Streamlit Cloud](https://streamlit.io/cloud).
3.  In Streamlit Cloud settings, add the `API_URL` secret pointing to your deployed API (e.g., `https://malaria-api.onrender.com`).

## 🔌 API Endpoints
- `POST /api/malaria-risk`: Get risk prediction and environmental features.
    - Body: `{"lat": 0.0, "lng": 30.0}`
- `POST /api/historical-weather`: Get historical climate data.

## ⚠️ Troubleshooting
- **Earth Engine Error**: Ensure your service account has "Earth Engine Resource Viewer" role and the API is enabled in Google Cloud Console.
- **Fallback Data**: If the API cannot connect to GEE, the app will use simulated data and show a warning. Check your credentials.
