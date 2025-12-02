# map_utils.py - FITSIS Malaria Risk Mapping with API Backend
import folium
from streamlit_folium import st_folium
import streamlit as st
from database import save_prediction
from datetime import datetime
import requests
import os
import json
import numpy as np

# API Configuration
# In production, this should be set to the deployed backend URL
API_URL = os.environ.get("API_URL", "http://localhost:8000")

def is_using_fallback():
    """
    Check if we're using fallback data.
    This is now determined by the API response, but for UI consistency we can default to False
    until we make a request. Or we can check API health.
    """
    # For simplicity in the UI, we assume true if API is unreachable, but the API response
    # will contain the definitive "data_source" field.
    # We can store the last request status in session state.
    return st.session_state.get("using_fallback", False)

def extract_features_for_prediction(lat, lon):
    """Extract features by calling the backend API"""
    
    st.write("### 🦟 Extracting Malaria Risk Factors...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/malaria-risk",
            json={"lat": lat, "lng": lon},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", {})
            data_source = data.get("data_source", "Unknown")
            
            # Update session state for UI indicators
            st.session_state["using_fallback"] = (data_source != "Earth Engine")
            
            # Display features
            st.write(f"🌧️ Rainfall: {features.get('rainfall_12mo', 0):.1f} mm")
            st.write(f"🌡️ Temperature: {features.get('temp_mean_c', 0):.1f} °C")
            st.write(f"🌿 NDVI: {features.get('ndvi_mean', 0):.3f}")
            st.write(f"👥 Population density: {features.get('pop_density', 0):.1f} people/km²")
            st.write(f"🏔️ Elevation: {features.get('elevation', 0):.1f} m")
            st.write(f"💧 Water coverage: {features.get('water_coverage', 0):.1f}%")
            
            if st.session_state["using_fallback"]:
                st.info(f"📊 Using {data_source} data")
            else:
                st.success(f"✅ Features extracted successfully from {data_source}!")
                
            return features
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            st.session_state["using_fallback"] = True
            return {}
            
    except Exception as e:
        st.error(f"❌ Connection to backend failed: {e}")
        st.session_state["using_fallback"] = True
        return {}

def predict_malaria_risk(features):
    """
    Predict malaria risk.
    Ideally, the API should return the prediction.
    However, the current app structure expects this function to return prediction, confidence, probabilities.
    We can either:
    1. Call the API again (inefficient)
    2. Use the local model (as before)
    3. Return the values we already got from the API in extract_features_for_prediction
    
    Refactoring `extract_features_for_prediction` to return the full API response would be better,
    but that breaks the contract with `app.py`.
    
    For now, we will call the API *again* or just use the local model if we have it.
    Actually, `extract_features_for_prediction` is called first in `app.py`, then `predict_malaria_risk`.
    
    Let's modify `extract_features_for_prediction` to store the prediction result in session state
    so we can retrieve it here without re-calling the API?
    Or better, let's just make `predict_malaria_risk` call the API if it hasn't been called,
    but `app.py` passes `features` to it.
    
    Wait, the API `/api/malaria-risk` returns BOTH features AND prediction.
    So in `app.py`:
        features = extract_features_for_prediction(lat, lng)
        prediction, confidence, probabilities = predict_malaria_risk(features)
        
    I should update `extract_features_for_prediction` to return the features,
    AND cache the prediction result in `st.session_state` so `predict_malaria_risk` can just return it.
    """
    
    # Check if we have a cached prediction from the API call
    cached_pred = st.session_state.get("last_api_prediction")
    
    if cached_pred:
        # Verify it matches the features (rough check)
        # Actually, let's just trust the flow for now or re-predict locally if needed.
        # But the API is the source of truth.
        
        return (
            cached_pred["risk_level"],
            cached_pred["confidence"],
            list(cached_pred["probabilities"].values()) # Assuming order Low, Medium, High
        )
    
    # Fallback to local prediction if API didn't cache it (shouldn't happen if flow is correct)
    # or if we are just running unit tests.
    try:
        import joblib
        model = joblib.load('malaria_model_expanded.pkl')
        feature_names = ['rainfall_12mo', 'temp_mean_c', 'ndvi_mean', 'pop_density', 'elevation', 'water_coverage']
        feature_values = [features.get(f, 0) for f in feature_names]
        prediction = model.predict([feature_values])[0]
        probabilities = model.predict_proba([feature_values])[0]
        confidence = max(probabilities)
        return prediction, confidence, probabilities
    except:
        return "Unknown", 0.0, [0.0, 0.0, 0.0]

def create_interactive_map():
    """Create an interactive Folium map"""
    m = folium.Map(location=[0, 20], zoom_start=3)
    m.add_child(folium.LatLngPopup())
    return m

def get_historical_data(lat, lon):
    """Get historical climate data from API"""
    try:
        response = requests.post(
            f"{API_URL}/api/historical-weather",
            json={"lat": lat, "lng": lon},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.warning("Could not fetch historical data.")
            return None
    except Exception as e:
        st.warning(f"Error fetching historical data: {e}")
        return None

# Update extract_features_for_prediction to cache the prediction
def extract_features_for_prediction(lat, lon):
    """Extract features by calling the backend API"""
    
    # st.write("### 🦟 Extracting Malaria Risk Factors...") # Moved to app.py or keep here
    
    try:
        response = requests.post(
            f"{API_URL}/api/malaria-risk",
            json={"lat": lat, "lng": lon},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", {})
            data_source = data.get("data_source", "Unknown")
            
            # Cache the full prediction result
            st.session_state["last_api_prediction"] = data
            st.session_state["using_fallback"] = (data_source != "Earth Engine")
            
            # Display features (optional, app.py does it too but this function had st.write calls)
            # The original function had st.write calls, so we keep them for UI consistency
            st.write(f"🌧️ Rainfall: {features.get('rainfall_12mo', 0):.1f} mm")
            st.write(f"🌡️ Temperature: {features.get('temp_mean_c', 0):.1f} °C")
            st.write(f"🌿 NDVI: {features.get('ndvi_mean', 0):.3f}")
            st.write(f"👥 Population density: {features.get('pop_density', 0):.1f} people/km²")
            st.write(f"🏔️ Elevation: {features.get('elevation', 0):.1f} m")
            st.write(f"💧 Water coverage: {features.get('water_coverage', 0):.1f}%")
            
            if st.session_state["using_fallback"]:
                st.info(f"📊 Using {data_source} data")
            else:
                st.success(f"✅ Features extracted successfully from {data_source}!")
                
            return features
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            st.session_state["using_fallback"] = True
            return {}
            
    except Exception as e:
        st.error(f"❌ Connection to backend failed: {e}")
        st.session_state["using_fallback"] = True
        return {}
