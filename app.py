# app.py
import streamlit as st
import pandas as pd
from auth import login_user, register_user, logout_user, check_auth
from map_utils import create_interactive_map, extract_features_for_prediction, predict_malaria_risk, get_historical_data
from charts import create_rainfall_chart, create_temperature_chart, create_feature_importance_chart, create_prediction_gauge
from database import save_prediction, get_user_predictions
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="Malaria Risk Predictor",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #2E86AB;
            text-align: center;
            margin-bottom: 2rem;
        }
        .risk-high {
            background-color: #ff6b6b;
            padding: 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        }
        .risk-medium {
            background-color: #ffd93d;
            padding: 10px;
            border-radius: 5px;
            color: black;
            font-weight: bold;
        }
        .risk-low {
            background-color: #6bcf7f;
            padding: 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">🦟 Malaria Risk Predictor</h1>', unsafe_allow_html=True)

    # Check authentication
    if not check_auth():
        show_auth_pages()
    else:
        show_main_app()

def show_auth_pages():
    """Show login/registration pages"""
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        login_user()
    
    with tab2:
        register_user()

def show_main_app():
    """Show the main application after login"""
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}! 👋")
        st.markdown("---")
        
        # Navigation with unique key
        page = st.radio("Navigate to:", 
                       ["Map Predictor", "Prediction History", "Account Info"],
                       key="main_navigation")
        
        st.markdown("---")
        if st.button("Logout", key="logout_button"):
            logout_user()
    
    # Main content based on navigation
    if page == "Map Predictor":
        show_map_predictor()
    elif page == "Prediction History":
        show_prediction_history()
    elif page == "Account Info":
        show_account_info()

def show_map_predictor():
    """Show the interactive map and prediction interface"""
    st.header("🌍 Interactive Malaria Risk Map")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Click on the map to select a location")
        
        # Create and display map with unique key
        m = create_interactive_map()
        map_data = st_folium(m, width=700, height=500, key="main_map")
        
        # Handle map clicks
        if map_data and map_data.get('last_clicked'):
            lat = map_data['last_clicked']['lat']
            lng = map_data['last_clicked']['lng']
            
            st.success(f"📍 Selected location: {lat:.4f}, {lng:.4f}")
            
            # Process the selected location
            process_location_prediction(lat, lng)
    
    with col2:
        st.subheader("How to Use:")
        st.markdown("""
        1. **Zoom** to your area of interest
        2. **Click** on any location on the map
        3. **Wait** for feature extraction
        4. **View** prediction results and charts
        
        The system will analyze:
        - 🌧️ Rainfall patterns
        - 🌡️ Temperature data  
        - 🌿 Vegetation (NDVI)
        - 👥 Population density
        - 🏔️ Elevation
        - 💧 Water bodies
        """)

def process_location_prediction(lat, lng):
    """Process prediction for a selected location"""
    with st.spinner("🔄 Extracting environmental features..."):
        features = extract_features_for_prediction(lat, lng)
    
    if features:
        # Display features with unique key
        st.subheader("📊 Extracted Features")
        feature_df = pd.DataFrame.from_dict(features, orient='index', columns=['Value'])
        st.dataframe(feature_df.style.format("{:.2f}"), key="features_table")
        
        # Make prediction
        with st.spinner("🤖 Analyzing malaria risk..."):
            prediction, confidence, probabilities = predict_malaria_risk(features)
        
        if prediction:
            # Display prediction result
            st.subheader("🎯 Prediction Result")
            
            # Risk indicator
            risk_class = f"risk-{prediction.lower()}"
            st.markdown(f'<div class="{risk_class}">Malaria Risk: {prediction}</div>', unsafe_allow_html=True)
            
            # Confidence gauge with unique key
            gauge_chart = create_prediction_gauge(prediction, confidence)
            st.plotly_chart(gauge_chart, use_container_width=True, key="prediction_gauge")
            
            # Save prediction to history
            import json
            features_json = json.dumps(features)
            save_prediction(st.session_state.user_id, lat, lng, prediction, confidence, features_json)
            
            # Show historical data charts
            st.subheader("📈 Historical Climate Data")
            historical_data = get_historical_data(lat, lng)
            
            if historical_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    rainfall_chart = create_rainfall_chart(historical_data)
                    st.plotly_chart(rainfall_chart, use_container_width=True, key="rainfall_chart")
                
                with col2:
                    temp_chart = create_temperature_chart(historical_data)
                    st.plotly_chart(temp_chart, use_container_width=True, key="temperature_chart")
                
                # Feature importance chart with unique key
                feature_chart = create_feature_importance_chart(features)
                st.plotly_chart(feature_chart, use_container_width=True, key="feature_chart")
            
            # Risk interpretation
            st.subheader("🔍 Risk Interpretation")
            if prediction == "High":
                st.warning("""
                **High Risk Area** - Consider:
                - Implementing mosquito control measures
                - Public health awareness campaigns
                - Regular monitoring and surveillance
                - Preventive medication if traveling
                """)
            elif prediction == "Medium":
                st.info("""
                **Medium Risk Area** - Consider:
                - Seasonal monitoring
                - Basic preventive measures
                - Community awareness programs
                """)
            else:
                st.success("""
                **Low Risk Area** - Maintain:
                - Basic surveillance
                - Preparedness for climate changes
                - Public health infrastructure
                """)

def show_prediction_history():
    """Show user's prediction history"""
    st.header("📋 Prediction History")
    
    predictions = get_user_predictions(st.session_state.user_id)
    
    if not predictions:
        st.info("No predictions made yet. Go to the map and click on locations to make predictions!")
    else:
        # Create dataframe from predictions
        history_data = []
        for pred in predictions:
            history_data.append({
                'Date': pred[7],
                'Latitude': pred[2],
                'Longitude': pred[3],
                'Prediction': pred[4],
                'Confidence': f"{pred[5]*100:.1f}%"
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, key="history_table")
        
        # Show some statistics - REMOVE THE 'key' PARAMETERS
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Predictions", len(predictions))  # ✅ Fixed
        with col2:
            high_risk = len([p for p in predictions if p[4] == 'High'])
            st.metric("High Risk Areas", high_risk)  # ✅ Fixed
        with col3:
            avg_confidence = sum([p[5] for p in predictions]) / len(predictions)
            st.metric("Average Confidence", f"{avg_confidence*100:.1f}%")  # ✅ Fixed

def show_account_info():
    """Show user account information"""
    st.header("👤 Account Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Profile")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**User ID:** {st.session_state.user_id}")
        
        # Get prediction stats
        predictions = get_user_predictions(st.session_state.user_id)
        st.write(f"**Predictions Made:** {len(predictions)}")
    
    with col2:
        st.subheader("About Malaria Predictor")
        st.markdown("""
        This app uses machine learning to predict malaria risk based on:
        
        - **Environmental factors**: Rainfall, temperature, vegetation
        - **Geographic features**: Elevation, water bodies
        - **Human factors**: Population density
        
        The model was trained on global malaria incidence data and environmental datasets from Google Earth Engine.
        """)

if __name__ == "__main__":
    main()