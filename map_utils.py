# map_utils.py
import ee
import pandas as pd
import joblib
import json
import folium
from streamlit_folium import st_folium
import streamlit as st
from database import save_prediction
from datetime import datetime, timedelta

# Initialize Earth Engine
try:
    ee.Initialize(project='siol-degradation')
except:
    st.error("Please authenticate Earth Engine first")

def extract_features_for_prediction(lat, lon):
    """Extract features for a given location for prediction"""
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

def create_interactive_map():
    """Create an interactive Folium map"""
    # Start with a default location (center of Africa)
    m = folium.Map(location=[0, 20], zoom_start=3)
    
    # Add click functionality
    m.add_child(folium.LatLngPopup())
    
    return m

def get_historical_data(lat, lon):
    """Get historical climate data for charts"""
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