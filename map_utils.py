# map_utils.py
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

def initialize_earth_engine():
    """Initialize Earth Engine with multiple authentication methods"""
    
    # Check if already initialized
    try:
        if ee.data._credentials is not None:
            # Test if the initialized credentials are still valid
            ee.Image('LANDSAT/LC08/C01/T1_SR/LC08_044034_20140318').bandNames().getInfo()
            st.success("✅ Earth Engine already initialized and working!")
            return True
    except:
        # Not properly initialized, continue with initialization
        pass
    
    try:
        # Method 1: Try service account authentication first
        st.info("🔄 Initializing Earth Engine...")
        
        # Get credentials from secrets
        service_account_email = st.secrets.get("EE_ACCOUNT")
        private_key = st.secrets.get("EE_PRIVATE_KEY")
        
        if not service_account_email or not private_key:
            st.error("❌ Earth Engine credentials not found in secrets")
            return False
        
        # Clean the private key
        private_key = private_key.strip()
        
        # Remove extra quotes if present
        if private_key.startswith('"') and private_key.endswith('"'):
            private_key = private_key[1:-1]
        
        # Ensure proper line endings
        private_key = private_key.replace('\\n', '\n')
        
        # Ensure the key has proper BEGIN/END markers
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
        if not private_key.endswith('-----END PRIVATE KEY-----'):
            private_key = private_key + '\n-----END PRIVATE KEY-----'
        
        # Create credentials
        credentials = ee.ServiceAccountCredentials(service_account_email, key_data=private_key)
        
        # Initialize Earth Engine
        ee.Initialize(credentials)
        
        # Test the connection
        try:
            # Simple test - get a small image collection
            test_image = ee.Image('LANDSAT/LC08/C01/T1_SR/LC08_044034_20140318')
            band_names = test_image.bandNames().getInfo()
            st.success(f"✅ Earth Engine initialized successfully! Available bands: {len(band_names)}")
            return True
        except Exception as test_error:
            st.error(f"❌ Earth Engine test failed: {test_error}")
            return False
            
    except Exception as e:
        st.error(f"❌ Failed to initialize Earth Engine: {str(e)}")
        
        # Provide helpful debugging information
        st.info("""
        **Troubleshooting steps:**
        1. Verify your service account email is correct
        2. Ensure the private key is properly formatted with correct line breaks
        3. Check that the service account has Earth Engine access
        4. Verify your project is enabled for Earth Engine API
        """)
        return False

# Initialize Earth Engine at module load
ee_initialized = initialize_earth_engine()

def check_ee_initialized():
    """Check if Earth Engine is properly initialized"""
    try:
        if ee.data._credentials is None:
            return False
        # Test with a simple operation
        ee.Image(1).getInfo()
        return True
    except:
        return False

def create_interactive_map():
    """Create an interactive Folium map"""
    # Start with a default location (center of Africa)
    m = folium.Map(location=[0, 20], zoom_start=3)
    
    # Add click functionality
    m.add_child(folium.LatLngPopup())
    
    return m

def extract_features_for_prediction(lat, lon):
    """Extract features for a given location for prediction"""
    
    if not check_ee_initialized():
        st.error("❌ Earth Engine not initialized. Cannot extract features.")
        return None
        
    try:
        point = ee.Geometry.Point([lon, lat]).buffer(5000)  # 5km buffer
        
        # Fix date handling - use current date properly
        current_date = datetime.now()
        end_date = current_date.strftime('%Y-%m-%d')
        start_date = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')  # 12 months back
        
        # Use ee.Date with proper string format
        end = ee.Date(end_date)
        start = ee.Date(start_date)

        # 1) Rainfall - mosquito breeding
        try:
            chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filterDate(start, end).select('precipitation')
            rain_sum = chirps.sum()
            rain_stat = rain_sum.reduceRegion(ee.Reducer.mean(), point, scale=5000).getInfo()
            rainfall = rain_stat.get('precipitation', 0)
            st.write(f"🌧️ Rainfall: {rainfall:.1f} mm")
        except Exception as e:
            st.write(f"⚠️ Rainfall data unavailable: {e}")
            rainfall = 0

        # 2) Temperature - mosquito development rate
        try:
            modis = ee.ImageCollection('MODIS/006/MOD11A2').select('LST_Day_1km').filterDate(start, end)
            temp_mean = modis.mean().multiply(0.02).subtract(273.15)
            temp_stat = temp_mean.reduceRegion(ee.Reducer.mean(), point, scale=1000).getInfo()
            temperature = temp_stat.get('LST_Day_1km', 0)
            st.write(f"🌡️ Temperature: {temperature:.1f} °C")
        except Exception as e:
            st.write(f"⚠️ Temperature data unavailable: {e}")
            temperature = 0

        # 3) NDVI - vegetation for mosquito resting
        try:
            ndvi_coll = ee.ImageCollection('MODIS/006/MOD13Q1').select('NDVI').filterDate(start, end)
            ndvi_mean = ndvi_coll.mean().multiply(0.0001)
            ndvi_stat = ndvi_mean.reduceRegion(ee.Reducer.mean(), point, scale=250).getInfo()
            ndvi = ndvi_stat.get('NDVI', 0)
            st.write(f"🌿 NDVI: {ndvi:.3f}")
        except Exception as e:
            st.write(f"⚠️ NDVI data unavailable: {e}")
            ndvi = 0

        # 4) Population density - human hosts
        try:
            # Try multiple population datasets
            pop_img = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq('year', 2020)).first()
            pop_stat = pop_img.reduceRegion(ee.Reducer.mean(), point, scale=100).getInfo()
            population = pop_stat.get('population', 0)
            
            if population == 0:
                # Fallback to GPW
                pop_img2 = ee.Image('CIESIN/GPWv411/GPW_Population_Density')
                pop_stat2 = pop_img2.reduceRegion(ee.Reducer.mean(), point, scale=1000).getInfo()
                population = pop_stat2.get('population_density', 0)
            
            st.write(f"👥 Population density: {population:.1f} people/km²")
        except Exception as e:
            st.write(f"⚠️ Population data unavailable: {e}")
            population = 0

        # 5) Elevation - affects temperature
        try:
            elev_img = ee.Image('USGS/SRTMGL1_003')
            elev_stat = elev_img.reduceRegion(ee.Reducer.mean(), point, scale=30).getInfo()
            elevation = elev_stat.get('elevation', 0)
            st.write(f"🏔️ Elevation: {elevation:.1f} m")
        except Exception as e:
            st.write(f"⚠️ Elevation data unavailable: {e}")
            elevation = 0

        # 6) Water bodies - mosquito breeding sites
        try:
            water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
            water_stat = water.reduceRegion(ee.Reducer.mean(), point, scale=30).getInfo()
            water_coverage = water_stat.get('occurrence', 0)
            st.write(f"💧 Water coverage: {water_coverage:.1f}%")
        except Exception as e:
            st.write(f"⚠️ Water coverage data unavailable: {e}")
            water_coverage = 0

        features = {
            'rainfall_12mo': rainfall,
            'temp_mean_c': temperature,
            'ndvi_mean': ndvi,
            'pop_density': population,
            'elevation': elevation,
            'water_coverage': water_coverage
        }
        
        return features
        
    except Exception as e:
        st.error(f"❌ Error extracting features: {e}")
        return None

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
        
        st.write(f"🎯 Prediction: {prediction} (Confidence: {confidence:.2f})")
        
        return prediction, confidence, probabilities
        
    except Exception as e:
        st.error(f"❌ Error making prediction: {e}")
        # Return default values if model fails
        return "Medium", 0.5, [0.33, 0.33, 0.34]

def get_historical_data(lat, lon):
    """Get historical climate data for charts"""
    
    if not check_ee_initialized():
        st.error("❌ Earth Engine not initialized. Cannot get historical data.")
        # Return sample data if EE fails
        return {
            'years': [2019, 2020, 2021, 2022, 2023],
            'rainfall': [800, 850, 780, 920, 870],
            'temperature': [25, 26, 24, 27, 25]
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

# Add this function to your map_utils.py for better mobile experience
def create_mobile_friendly_map():
    """Create a mobile-optimized map"""
    import folium
    
    # Center on Africa with mobile-appropriate zoom
    m = folium.Map(
        location=[6.3690, 20.3983], 
        zoom_start=3,
        tiles='CartoDB positron'  # Lighter tiles for mobile
    )
    
    # Add mobile-friendly popups
    m.add_child(folium.LatLngPopup())
    
    return m
