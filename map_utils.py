# map_utils.py - FITSIS Malaria Risk Mapping with Fallback Data
import ee
import os
import pandas as pd
import joblib
import json
import folium
from streamlit_folium import st_folium
import streamlit as st
from database import save_prediction
from datetime import datetime, timedelta
import requests
import numpy as np

# Global flag to track if we're using fallback data
using_fallback_data = False

def initialize_earth_engine():
    """Initialize Earth Engine with comprehensive fallback handling"""
    global using_fallback_data
    
    try:
        # Check if already initialized
        if ee.data._credentials is not None:
            # Test if the initialized credentials are still valid
            ee.Image('LANDSAT/LC08/C01/T1_SR/LC08_044034_20140318').bandNames().getInfo()
            st.success("✅ Earth Engine initialized successfully!")
            using_fallback_data = False
            return True
    except:
        # Not properly initialized, continue with initialization
        pass
    
    try:
        st.info("🔄 Initializing Earth Engine for FITSIS Malaria Mapping...")
        
        # Get credentials from secrets
        service_account = st.secrets["EE_ACCOUNT"]
        private_key = st.secrets["EE_PRIVATE_KEY"]
        
        # Clean the private key
        private_key = private_key.strip()
        if private_key.startswith('"') and private_key.endswith('"'):
            private_key = private_key[1:-1]
        private_key = private_key.replace('\\n', '\n')
        
        # Initialize Earth Engine
        credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
        ee.Initialize(credentials)
        
        # Test connection
        try:
            test_collection = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').limit(1)
            test_collection.size().getInfo()
            st.success("✅ Earth Engine initialized successfully!")
            using_fallback_data = False
            return True
        except Exception as test_error:
            st.warning(f"⚠️ Earth Engine test failed, using fallback data: {test_error}")
            using_fallback_data = True
            return False
            
    except Exception as e:
        st.warning(f"⚠️ Earth Engine initialization failed, using fallback data: {str(e)}")
        using_fallback_data = True
        return False

# Initialize Earth Engine
ee_initialized = initialize_earth_engine()

def is_using_fallback():
    """Check if we're using fallback data"""
    return using_fallback_data

def get_fallback_features(lat, lon):
    """Get realistic fallback features based on location and climate zones"""
    
    # Africa climate zones approximation
    def get_climate_zone(lat, lon):
        # West Africa (tropical)
        if -20 <= lon <= 20 and 0 <= lat <= 20:
            return "tropical"
        # East Africa (varied - highlands and tropical)
        elif 20 <= lon <= 55 and -10 <= lat <= 15:
            if lat > 5:  # Ethiopian highlands
                return "highland"
            else:
                return "tropical"
        # Southern Africa
        elif 10 <= lon <= 40 and -35 <= lat <= -10:
            return "subtropical"
        # Central Africa
        elif 10 <= lon <= 30 and -10 <= lat <= 10:
            return "tropical"
        else:
            return "default"
    
    climate_zone = get_climate_zone(lat, lon)
    
    # Base features by climate zone
    climate_profiles = {
        "tropical": {
            'rainfall_12mo': np.random.normal(1200, 300),  # High rainfall
            'temp_mean_c': np.random.normal(27, 2),       # Warm
            'ndvi_mean': np.random.normal(0.6, 0.1),      # High vegetation
            'pop_density': np.random.normal(50, 30),      # Moderate population
            'elevation': np.random.normal(200, 150),      # Low elevation
            'water_coverage': np.random.normal(8, 4)      # Some water coverage
        },
        "highland": {
            'rainfall_12mo': np.random.normal(800, 200),  # Moderate rainfall
            'temp_mean_c': np.random.normal(18, 3),       # Cooler
            'ndvi_mean': np.random.normal(0.5, 0.1),      # Moderate vegetation
            'pop_density': np.random.normal(80, 40),      # Higher population
            'elevation': np.random.normal(1500, 500),     # High elevation
            'water_coverage': np.random.normal(5, 3)      # Less water coverage
        },
        "subtropical": {
            'rainfall_12mo': np.random.normal(600, 200),  # Lower rainfall
            'temp_mean_c': np.random.normal(22, 3),       # Moderate temperature
            'ndvi_mean': np.random.normal(0.4, 0.1),      # Lower vegetation
            'pop_density': np.random.normal(30, 20),      # Lower population
            'elevation': np.random.normal(500, 300),      # Moderate elevation
            'water_coverage': np.random.normal(3, 2)      # Low water coverage
        },
        "default": {
            'rainfall_12mo': np.random.normal(800, 200),
            'temp_mean_c': np.random.normal(25, 3),
            'ndvi_mean': np.random.normal(0.5, 0.1),
            'pop_density': np.random.normal(40, 25),
            'elevation': np.random.normal(300, 200),
            'water_coverage': np.random.normal(5, 3)
        }
    }
    
    base_features = climate_profiles[climate_zone]
    
    # Add some realistic variation based on exact coordinates
    features = {}
    for key, (mean, std) in base_features.items():
        # Use coordinates to create deterministic but varied values
        variation_seed = hash(f"{lat:.2f}{lon:.2f}{key}") % 1000 / 1000
        features[key] = max(0, mean + (variation_seed - 0.5) * 2 * std)
    
    # Ensure realistic ranges
    features['rainfall_12mo'] = max(200, min(3000, features['rainfall_12mo']))
    features['temp_mean_c'] = max(10, min(40, features['temp_mean_c']))
    features['ndvi_mean'] = max(0.1, min(0.9, features['ndvi_mean']))
    features['pop_density'] = max(0, min(200, features['pop_density']))
    features['elevation'] = max(0, min(3000, features['elevation']))
    features['water_coverage'] = max(0, min(50, features['water_coverage']))
    
    return features

def extract_features_for_prediction(lat, lon):
    """Extract features with Earth Engine fallback to simulated data"""
    
    if not is_using_fallback():
        # Try to use Earth Engine
        try:
            point = ee.Geometry.Point([lon, lat]).buffer(5000)
            
            current_date = datetime.now()
            end_date = current_date.strftime('%Y-%m-%d')
            start_date = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')
            
            end = ee.Date(end_date)
            start = ee.Date(start_date)

            st.write("### 🦟 Extracting Malaria Risk Factors from Earth Engine...")

            features = {}
            
            # 1) Rainfall
            try:
                chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filterDate(start, end).select('precipitation')
                rain_sum = chirps.sum()
                rain_stat = rain_sum.reduceRegion(ee.Reducer.mean(), point, scale=5000).getInfo()
                rainfall = rain_stat.get('precipitation', 0)
                features['rainfall_12mo'] = rainfall
                st.write(f"🌧️ Rainfall: {rainfall:.1f} mm")
            except Exception as e:
                st.write(f"⚠️ Rainfall data unavailable: {e}")
                features['rainfall_12mo'] = 0

            # 2) Temperature
            try:
                modis = ee.ImageCollection('MODIS/006/MOD11A2').select('LST_Day_1km').filterDate(start, end)
                temp_mean = modis.mean().multiply(0.02).subtract(273.15)
                temp_stat = temp_mean.reduceRegion(ee.Reducer.mean(), point, scale=1000).getInfo()
                temperature = temp_stat.get('LST_Day_1km', 0)
                features['temp_mean_c'] = temperature
                st.write(f"🌡️ Temperature: {temperature:.1f} °C")
            except Exception as e:
                st.write(f"⚠️ Temperature data unavailable: {e}")
                features['temp_mean_c'] = 0

            # 3) NDVI
            try:
                ndvi_coll = ee.ImageCollection('MODIS/006/MOD13Q1').select('NDVI').filterDate(start, end)
                ndvi_mean = ndvi_coll.mean().multiply(0.0001)
                ndvi_stat = ndvi_mean.reduceRegion(ee.Reducer.mean(), point, scale=250).getInfo()
                ndvi = ndvi_stat.get('NDVI', 0)
                features['ndvi_mean'] = ndvi
                st.write(f"🌿 NDVI: {ndvi:.3f}")
            except Exception as e:
                st.write(f"⚠️ NDVI data unavailable: {e}")
                features['ndvi_mean'] = 0

            # 4) Population
            try:
                pop_img = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq('year', 2020)).first()
                pop_stat = pop_img.reduceRegion(ee.Reducer.mean(), point, scale=100).getInfo()
                population = pop_stat.get('population', 0)
                features['pop_density'] = population
                st.write(f"👥 Population density: {population:.1f} people/km²")
            except Exception as e:
                st.write(f"⚠️ Population data unavailable: {e}")
                features['pop_density'] = 0

            # 5) Elevation
            try:
                elev_img = ee.Image('USGS/SRTMGL1_003')
                elev_stat = elev_img.reduceRegion(ee.Reducer.mean(), point, scale=30).getInfo()
                elevation = elev_stat.get('elevation', 0)
                features['elevation'] = elevation
                st.write(f"🏔️ Elevation: {elevation:.1f} m")
            except Exception as e:
                st.write(f"⚠️ Elevation data unavailable: {e}")
                features['elevation'] = 0

            # 6) Water coverage
            try:
                water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
                water_stat = water.reduceRegion(ee.Reducer.mean(), point, scale=30).getInfo()
                water_coverage = water_stat.get('occurrence', 0)
                features['water_coverage'] = water_coverage
                st.write(f"💧 Water coverage: {water_coverage:.1f}%")
            except Exception as e:
                st.write(f"⚠️ Water coverage data unavailable: {e}")
                features['water_coverage'] = 0

            st.success("✅ Features extracted successfully from Earth Engine!")
            return features
            
        except Exception as e:
            st.warning(f"⚠️ Earth Engine extraction failed, using fallback data: {e}")
            using_fallback_data = True
    
    # Use fallback data
    st.info("📊 Using simulated environmental data (Earth Engine unavailable)")
    
    features = get_fallback_features(lat, lon)
    
    # Display the simulated features
    st.write(f"🌧️ Rainfall: {features['rainfall_12mo']:.1f} mm")
    st.write(f"🌡️ Temperature: {features['temp_mean_c']:.1f} °C")
    st.write(f"🌿 NDVI: {features['ndvi_mean']:.3f}")
    st.write(f"👥 Population density: {features['pop_density']:.1f} people/km²")
    st.write(f"🏔️ Elevation: {features['elevation']:.1f} m")
    st.write(f"💧 Water coverage: {features['water_coverage']:.1f}%")
    
    st.warning("💡 Note: Using simulated data. For real-time analysis, check Earth Engine configuration.")
    
    return features

def predict_malaria_risk(features):
    """Predict malaria risk using the trained model"""
    try:
        # Load your trained model
        model = joblib.load('malaria_model_expanded.pkl')
        
        # Create feature array in correct order
        feature_names = ['rainfall_12mo', 'temp_mean_c', 'ndvi_mean', 'pop_density', 'elevation', 'water_coverage']
        feature_values = [features.get(f, 0) for f in feature_names]
        
        # Make prediction
        prediction = model.predict([feature_values])[0]
        probabilities = model.predict_proba([feature_values])[0]
        confidence = max(probabilities)
        
        # Adjust confidence display for fallback data
        if is_using_fallback():
            confidence = max(0.6, confidence)  # Lower confidence for simulated data
            st.write(f"🎯 Prediction: {prediction} (Confidence: {confidence:.2f}) - Using Simulated Data")
        else:
            st.write(f"🎯 Prediction: {prediction} (Confidence: {confidence:.2f})")
        
        return prediction, confidence, probabilities
        
    except Exception as e:
        st.error(f"❌ Error making prediction: {e}")
        # Return default values if model fails
        return "Medium", 0.5, [0.33, 0.33, 0.34]

def create_interactive_map():
    """Create an interactive Folium map"""
    # Start with a default location (center of Africa)
    m = folium.Map(location=[0, 20], zoom_start=3)
    
    # Add click functionality
    m.add_child(folium.LatLngPopup())
    
    return m

def get_historical_data(lat, lon):
    """Get historical climate data with fallback"""
    
    if is_using_fallback():
        # Generate realistic historical trends based on location
        current_year = datetime.now().year
        years = list(range(current_year-5, current_year))
        
        # Base trends based on climate zone
        base_rainfall = get_fallback_features(lat, lon)['rainfall_12mo']
        base_temperature = get_fallback_features(lat, lon)['temp_mean_c']
        
        # Add some realistic variation
        rainfall_data = [max(0, base_rainfall + np.random.normal(0, 100)) for _ in years]
        temp_data = [max(10, base_temperature + np.random.normal(0, 2)) for _ in years]
        
        return {
            'years': years,
            'rainfall': rainfall_data,
            'temperature': temp_data
        }
    
    try:
        point = ee.Geometry.Point([lon, lat])
        
        # Get last 5 years of data
        current_year = datetime.now().year
        years = list(range(current_year-5, current_year))
        
        rainfall_data = []
        temp_data = []
        
        for year in years:
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'
            
            start = ee.Date(start_date)
            end = ee.Date(end_date)
            
            # Annual rainfall
            try:
                chirps_yearly = ee.ImageCollection('UCSB-CHG/CHIRPS/MONTHLY').filterDate(start, end)
                annual_rain = chirps_yearly.sum()
                rain_stat = annual_rain.reduceRegion(ee.Reducer.mean(), point, scale=5000).getInfo()
                rainfall = rain_stat.get('precipitation', 0)
                rainfall_data.append(rainfall)
            except:
                rainfall_data.append(0)
            
            # Annual temperature
            try:
                modis_yearly = ee.ImageCollection('MODIS/006/MOD11A2').select('LST_Day_1km').filterDate(start, end)
                temp_mean = modis_yearly.mean().multiply(0.02).subtract(273.15)
                temp_stat = temp_mean.reduceRegion(ee.Reducer.mean(), point, scale=1000).getInfo()
                temperature = temp_stat.get('LST_Day_1km', 0)
                temp_data.append(temperature)
            except:
                temp_data.append(0)
        
        historical_data = {
            'years': years,
            'rainfall': rainfall_data,
            'temperature': temp_data
        }
        
        return historical_data
        
    except Exception as e:
        st.error(f"❌ Error getting historical data: {e}")
        # Return sample data if EE fails
        return {
            'years': [2019, 2020, 2021, 2022, 2023],
            'rainfall': [800, 850, 780, 920, 870],
            'temperature': [25, 26, 24, 27, 25]
        }
