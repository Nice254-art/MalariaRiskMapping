import os
import json
import ee
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import joblib
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Malaria Risk Mapping API")

# --- Earth Engine Initialization ---
def initialize_earth_engine():
    """Initialize Earth Engine using service account credentials."""
    try:
        service_account = os.environ.get("EE_SERVICE_ACCOUNT")
        private_key = os.environ.get("EE_PRIVATE_KEY")

        if not service_account or not private_key:
            print("Warning: EE_SERVICE_ACCOUNT or EE_PRIVATE_KEY not set. GEE features will fail.")
            return False

        # Clean the private key if needed (handle newlines)
        private_key = private_key.replace('\\n', '\n')
        
        credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
        ee.Initialize(credentials)
        print("Earth Engine initialized successfully.")
        return True
    except Exception as e:
        print(f"Failed to initialize Earth Engine: {e}")
        return False

# Initialize on startup
ee_initialized = initialize_earth_engine()

# --- Models ---
class LocationRequest(BaseModel):
    lat: float
    lng: float

class PredictionResponse(BaseModel):
    risk_level: str
    confidence: float
    features: Dict[str, float]
    probabilities: Dict[str, float]
    data_source: str

class HistoricalDataResponse(BaseModel):
    years: list[int]
    rainfall: list[float]
    temperature: list[float]

# --- ML Model Loading ---
try:
    model = joblib.load('malaria_model_expanded.pkl')
    print("ML Model loaded successfully.")
except Exception as e:
    print(f"Failed to load ML model: {e}")
    model = None

# --- Helper Functions ---
def get_ee_features(lat: float, lng: float) -> Dict[str, float]:
    """Extract features from Earth Engine."""
    if not ee_initialized:
        raise Exception("Earth Engine not initialized")

    point = ee.Geometry.Point([lng, lat]).buffer(5000)
    
    current_date = datetime.now()
    end_date = current_date.strftime('%Y-%m-%d')
    start_date = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')
    
    start = ee.Date(start_date)
    end = ee.Date(end_date)

    features = {}

    # 1. Rainfall (CHIRPS)
    try:
        chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filterDate(start, end).select('precipitation')
        rain_sum = chirps.sum()
        rain_stat = rain_sum.reduceRegion(ee.Reducer.mean(), point, scale=5000).getInfo()
        features['rainfall_12mo'] = rain_stat.get('precipitation', 0)
    except:
        features['rainfall_12mo'] = 0.0

    # 2. Temperature (MODIS)
    try:
        modis = ee.ImageCollection('MODIS/006/MOD11A2').select('LST_Day_1km').filterDate(start, end)
        temp_mean = modis.mean().multiply(0.02).subtract(273.15)
        temp_stat = temp_mean.reduceRegion(ee.Reducer.mean(), point, scale=1000).getInfo()
        features['temp_mean_c'] = temp_stat.get('LST_Day_1km', 0)
    except:
        features['temp_mean_c'] = 0.0

    # 3. NDVI (MODIS)
    try:
        ndvi_coll = ee.ImageCollection('MODIS/006/MOD13Q1').select('NDVI').filterDate(start, end)
        ndvi_mean = ndvi_coll.mean().multiply(0.0001)
        ndvi_stat = ndvi_mean.reduceRegion(ee.Reducer.mean(), point, scale=250).getInfo()
        features['ndvi_mean'] = ndvi_stat.get('NDVI', 0)
    except:
        features['ndvi_mean'] = 0.0

    # 4. Population (WorldPop)
    try:
        pop_img = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq('year', 2020)).first()
        pop_stat = pop_img.reduceRegion(ee.Reducer.mean(), point, scale=100).getInfo()
        features['pop_density'] = pop_stat.get('population', 0)
    except:
        features['pop_density'] = 0.0

    # 5. Elevation (SRTM)
    try:
        elev_img = ee.Image('USGS/SRTMGL1_003')
        elev_stat = elev_img.reduceRegion(ee.Reducer.mean(), point, scale=30).getInfo()
        features['elevation'] = elev_stat.get('elevation', 0)
    except:
        features['elevation'] = 0.0

    # 6. Water Coverage (JRC)
    try:
        water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
        water_stat = water.reduceRegion(ee.Reducer.mean(), point, scale=30).getInfo()
        features['water_coverage'] = water_stat.get('occurrence', 0)
    except:
        features['water_coverage'] = 0.0

    return features

def get_fallback_features(lat: float, lng: float) -> Dict[str, float]:
    """Generate fallback features if EE fails."""
    # Simplified fallback logic based on original code
    np.random.seed(int(lat*100 + lng*100))
    return {
        'rainfall_12mo': max(200, np.random.normal(800, 200)),
        'temp_mean_c': max(10, np.random.normal(25, 3)),
        'ndvi_mean': max(0.1, min(0.9, np.random.normal(0.5, 0.1))),
        'pop_density': max(0, np.random.normal(40, 25)),
        'elevation': max(0, np.random.normal(300, 200)),
        'water_coverage': max(0, np.random.normal(5, 3))
    }

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "online", "service": "Malaria Risk Mapping API"}

@app.post("/api/malaria-risk", response_model=PredictionResponse)
def predict_risk(req: LocationRequest):
    features = {}
    data_source = "Earth Engine"
    
    try:
        features = get_ee_features(req.lat, req.lng)
    except Exception as e:
        print(f"EE Error: {e}")
        features = get_fallback_features(req.lat, req.lng)
        data_source = "Simulated (Fallback)"

    # Predict
    if model:
        feature_names = ['rainfall_12mo', 'temp_mean_c', 'ndvi_mean', 'pop_density', 'elevation', 'water_coverage']
        feature_values = [features.get(f, 0) for f in feature_names]
        
        prediction = model.predict([feature_values])[0]
        probs = model.predict_proba([feature_values])[0]
        confidence = float(max(probs))
        
        prob_dict = {
            "Low": float(probs[0]) if len(probs) > 0 else 0,
            "Medium": float(probs[1]) if len(probs) > 1 else 0,
            "High": float(probs[2]) if len(probs) > 2 else 0
        }
    else:
        prediction = "Unknown"
        confidence = 0.0
        prob_dict = {}

    return {
        "risk_level": prediction,
        "confidence": confidence,
        "features": features,
        "probabilities": prob_dict,
        "data_source": data_source
    }

@app.post("/api/historical-weather", response_model=HistoricalDataResponse)
def get_historical_weather(req: LocationRequest):
    # For now, implementing the fallback logic or EE logic if available
    # This mirrors the original get_historical_data function
    
    years = []
    rainfall_data = []
    temp_data = []
    
    current_year = datetime.now().year
    years = list(range(current_year-5, current_year))

    if ee_initialized:
        try:
            point = ee.Geometry.Point([req.lng, req.lat])
            for year in years:
                start = ee.Date(f'{year}-01-01')
                end = ee.Date(f'{year}-12-31')
                
                # Rainfall
                try:
                    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/MONTHLY').filterDate(start, end)
                    rain = chirps.sum().reduceRegion(ee.Reducer.mean(), point, scale=5000).getInfo().get('precipitation', 0)
                    rainfall_data.append(rain)
                except:
                    rainfall_data.append(0)
                
                # Temp
                try:
                    modis = ee.ImageCollection('MODIS/006/MOD11A2').select('LST_Day_1km').filterDate(start, end)
                    temp = modis.mean().multiply(0.02).subtract(273.15).reduceRegion(ee.Reducer.mean(), point, scale=1000).getInfo().get('LST_Day_1km', 0)
                    temp_data.append(temp)
                except:
                    temp_data.append(0)
        except:
             # Fallback if EE fails during loop
             pass

    # If data is empty (EE failed or not initialized), use fallback
    if not rainfall_data or sum(rainfall_data) == 0:
        base_rain = 800
        base_temp = 25
        rainfall_data = [max(0, base_rain + np.random.normal(0, 100)) for _ in years]
        temp_data = [max(10, base_temp + np.random.normal(0, 2)) for _ in years]

    return {
        "years": years,
        "rainfall": rainfall_data,
        "temperature": temp_data
    }
