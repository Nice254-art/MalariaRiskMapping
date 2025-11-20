import streamlit as st
import ee
import json
import os
from google.oauth2 import service_account

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

def create_interactive_map(lat, lon, zoom=10):
    """Create an interactive map with Earth Engine layers"""
    
    if not check_ee_initialized():
        st.error("❌ Earth Engine not initialized. Cannot create map.")
        return None
    
    try:
        import folium
        
        # Create a Folium map
        m = folium.Map(location=[lat, lon], zoom_start=zoom)
        
        # Add Earth Engine layers here
        # Example: Add a simple NDVI layer
        try:
            # Get a recent Landsat image
            landsat = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
                .filterBounds(ee.Geometry.Point(lon, lat)) \
                .filterDate('2020-01-01', '2020-12-31') \
                .sort('CLOUD_COVER') \
                .first()
            
            # Calculate NDVI
            ndvi = landsat.normalizedDifference(['B5', 'B4']).rename('NDVI')
            
            # Add NDVI layer to map
            ndvi_params = {
                'min': -1,
                'max': 1,
                'palette': ['blue', 'white', 'green']
            }
            
            # This would normally be added via folium, but for now we'll keep it simple
            st.info("✅ Earth Engine layers available for display")
            
        except Exception as layer_error:
            st.warning(f"⚠️ Could not load Earth Engine layers: {layer_error}")
        
        return m
        
    except Exception as e:
        st.error(f"❌ Error creating map: {e}")
        return None

def extract_features_for_prediction(lat, lon, date):
    """Extract Earth Engine features for malaria prediction"""
    
    if not check_ee_initialized():
        st.error("❌ Earth Engine not initialized. Cannot extract features.")
        return None
    
    try:
        # Create a point geometry
        point = ee.Geometry.Point(lon, lat)
        
        # Define the date range (1 month around the selected date)
        start_date = ee.Date(date).advance(-15, 'day')
        end_date = ee.Date(date).advance(15, 'day')
        
        features = {}
        
        # Extract temperature data (MOD11A1.006 Terra Land Surface Temperature)
        temp_collection = ee.ImageCollection('MODIS/006/MOD11A1') \
            .filterBounds(point) \
            .filterDate(start_date, end_date)
        
        if temp_collection.size().getInfo() > 0:
            temp_image = temp_collection.mean()
            lst_day = temp_image.select('LST_Day_1km')
            scale = 0.02  # Scale factor for Kelvin to Celsius
            offset = -273.15  # Kelvin to Celsius offset
            
            # Get temperature at point
            temp_value = lst_day.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=1000
            ).getInfo()
            
            if 'LST_Day_1km' in temp_value:
                features['temperature'] = temp_value['LST_Day_1km'] * scale + offset
        
        # Extract precipitation data (CHIRPS Daily)
        precip_collection = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterBounds(point) \
            .filterDate(start_date, end_date)
        
        if precip_collection.size().getInfo() > 0:
            precip_image = precip_collection.mean()
            precip_value = precip_image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=5000
            ).getInfo()
            
            if 'precipitation' in precip_value:
                features['precipitation'] = precip_value['precipitation']
        
        # Extract elevation data (SRTM)
        elevation = ee.Image('USGS/SRTMGL1_003')
        elev_value = elevation.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=30
        ).getInfo()
        
        if 'elevation' in elev_value:
            features['elevation'] = elev_value['elevation']
        
        # Extract NDVI (Normalized Difference Vegetation Index)
        landsat_collection = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
            .filterBounds(point) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUD_COVER', 20))
        
        if landsat_collection.size().getInfo() > 0:
            landsat_image = landsat_collection.mean()
            ndvi = landsat_image.normalizedDifference(['B5', 'B4']).rename('NDVI')
            ndvi_value = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=30
            ).getInfo()
            
            if 'NDVI' in ndvi_value:
                features['ndvi'] = ndvi_value['NDVI']
        
        st.success("✅ Features extracted successfully from Earth Engine")
        return features
        
    except Exception as e:
        st.error(f"❌ Error extracting features: {e}")
        return None
