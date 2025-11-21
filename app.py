# app.py - Mobile Responsive Malaria Risk Predictor
import streamlit as st
import pandas as pd
from auth import login_user, register_user, logout_user, check_auth
from map_utils import create_interactive_map, extract_features_for_prediction, predict_malaria_risk, get_historical_data, is_using_fallback
from charts import create_rainfall_chart, create_temperature_chart, create_feature_importance_chart, create_prediction_gauge
from database import save_prediction, get_user_predictions
from streamlit_folium import st_folium

# Mobile-first page configuration
st.set_page_config(
    page_title="FITSIS Malaria Risk Predictor",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Mobile-responsive CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main > div {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        /* Stack columns on mobile */
        [data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
        }
        
        /* Adjust map height for mobile */
        .folium-map {
            height: 300px !important;
        }
        
        /* Responsive text sizes */
        .main-header {
            font-size: 1.8rem !important;
            text-align: center;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        /* Mobile-friendly buttons */
        .stButton > button {
            width: 100% !important;
            margin: 0.2rem 0;
            font-size: 16px !important;
        }
        
        /* Prevent zoom on iOS inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            font-size: 16px !important;
        }
        
        /* Compact cards for mobile */
        .risk-card {
            border-radius: 8px;
            padding: 0.8rem;
            margin: 0.3rem 0;
            font-size: 0.9rem;
        }
        
        /* Mobile table styling */
        .dataframe {
            font-size: 0.8rem;
        }
    }
    
    /* Tablet adjustments */
    @media (min-width: 769px) and (max-width: 1024px) {
        .folium-map {
            height: 400px !important;
        }
        .main-header {
            font-size: 2.2rem !important;
        }
    }
    
    /* Desktop adjustments */
    @media (min-width: 1025px) {
        .folium-map {
            height: 500px !important;
        }
        .main-header {
            font-size: 2.5rem !important;
        }
    }
    
    /* General mobile-friendly styles */
    .main-header {
        color: #2E86AB;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    
    .risk-card {
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .risk-high {
        background-color: #ff6b6b;
        border-left: 5px solid #dc3545;
        color: white;
        font-weight: bold;
    }
    
    .risk-medium {
        background-color: #ffd93d;
        border-left: 5px solid #ffc107;
        color: black;
        font-weight: bold;
    }
    
    .risk-low {
        background-color: #6bcf7f;
        border-left: 5px solid #28a745;
        color: white;
        font-weight: bold;
    }
    
    .data-source-badge {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .data-source-live {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    
    .data-source-simulated {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    
    /* Compact mobile layouts */
    .mobile-compact {
        padding: 0.5rem;
    }
    
    /* Touch-friendly elements */
    .touch-target {
        min-height: 44px;
        min-width: 44px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header with responsive design
    st.markdown('<h1 class="main-header">🦟 FITSIS Malaria Risk Predictor</h1>', unsafe_allow_html=True)

    # Check authentication
    if not check_auth():
        show_auth_pages()
    else:
        show_main_app()

def show_auth_pages():
    """Show login/registration pages with mobile optimization"""
    # Use tabs for mobile-friendly auth
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        login_user()
    
    with tab2:
        register_user()

def show_main_app():
    """Show the main application after login"""
    # Mobile-optimized sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}! 👋")
        st.markdown("---")
        
        # Data source status
        display_data_source_status()
        st.markdown("---")
        
        # Navigation with touch-friendly buttons
        st.subheader("Navigation")
        page = st.radio("Go to:", 
                       ["🗺️ Map Predictor", "📋 Prediction History", "👤 Account Info"],
                       key="main_navigation",
                       label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, key="logout_button"):
            logout_user()
    
    # Main content based on navigation
    if page == "🗺️ Map Predictor":
        show_map_predictor()
    elif page == "📋 Prediction History":
        show_prediction_history()
    elif page == "👤 Account Info":
        show_account_info()

def display_data_source_status():
    """Display current data source status"""
    if is_using_fallback():
        st.warning("""
        **🔸 Data Source: Simulated**
        - Using climate pattern estimates
        - Demo mode active
        - Functional but limited accuracy
        """)
        
        # Quick reconnect option
        if st.button("🔄 Connect to Earth Engine", use_container_width=True, key="reconnect_ee"):
            st.rerun()
    else:
        st.success("""
        **🔹 Data Source: Earth Engine**
        - Real-time satellite data
        - Live environmental monitoring
        - Maximum accuracy
        """)

def show_map_predictor():
    """Show the interactive map and prediction interface with mobile optimization"""
    st.header("🌍 Interactive Malaria Risk Map")
    
    # Responsive columns that stack on mobile
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 Select Location")
        st.markdown("Tap on the map below to select a location for analysis")
        
        # Create and display responsive map
        m = create_interactive_map()
        map_data = st_folium(m, width=None, height=400, key="main_map")
        
        # Handle map clicks
        if map_data and map_data.get('last_clicked'):
            lat = map_data['last_clicked']['lat']
            lng = map_data['last_clicked']['lng']
            
            st.success(f"📍 Selected: {lat:.4f}, {lng:.4f}")
            
            # Process the selected location
            process_location_prediction(lat, lng)
    
    with col2:
        st.subheader("ℹ️ How to Use")
        st.markdown("""
        1. **Zoom** to your area
        2. **Tap** any location
        3. **Wait** for analysis
        4. **View** results
        
        **Analyzed Factors:**
        - 🌧️ Rainfall patterns
        - 🌡️ Temperature  
        - 🌿 Vegetation
        - 👥 Population
        - 🏔️ Elevation
        - 💧 Water bodies
        """)

def process_location_prediction(lat, lng):
    """Process prediction for a selected location with enhanced data source handling"""
    with st.spinner("🔄 Extracting environmental features..."):
        features = extract_features_for_prediction(lat, lng)
    
    if features:
        # Display data source prominently
        display_prediction_data_source()
        
        # Display features in mobile-friendly format
        st.subheader("📊 Environmental Features")
        
        # Use columns for better mobile display
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🌧️ Rainfall", f"{features.get('rainfall_12mo', 0):.1f} mm")
            st.metric("🌡️ Temperature", f"{features.get('temp_mean_c', 0):.1f}°C")
            st.metric("🌿 NDVI", f"{features.get('ndvi_mean', 0):.3f}")
        
        with col2:
            st.metric("👥 Population", f"{features.get('pop_density', 0):.0f}/km²")
            st.metric("🏔️ Elevation", f"{features.get('elevation', 0):.0f} m")
            st.metric("💧 Water Cover", f"{features.get('water_coverage', 0):.1f}%")
        
        # Make prediction
        with st.spinner("🤖 Analyzing malaria risk..."):
            prediction, confidence, probabilities = predict_malaria_risk(features)
        
        if prediction:
            # Display prediction result
            st.subheader("🎯 Risk Assessment")
            
            # Risk indicator card
            risk_class = f"risk-{prediction.lower()}"
            st.markdown(f'''
            <div class="risk-card {risk_class}">
                <h3>Malaria Risk: {prediction}</h3>
                <p><strong>Confidence:</strong> {confidence:.1%}</p>
                <p><strong>Location:</strong> {lat:.4f}, {lng:.4f}</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # Confidence gauge
            gauge_chart = create_prediction_gauge(prediction, confidence)
            st.plotly_chart(gauge_chart, use_container_width=True, key="prediction_gauge")
            
            # Enhanced risk interpretation
            show_enhanced_risk_interpretation(prediction, confidence, is_using_fallback())
            
            # Save prediction to history
            import json
            features_json = json.dumps(features)
            save_prediction(st.session_state.user_id, lat, lng, prediction, confidence, features_json)
            
            # Show charts in mobile-friendly tabs
            show_prediction_charts(lat, lng, features, probabilities, prediction)

def display_prediction_data_source():
    """Display data source information for the current prediction"""
    if is_using_fallback():
        st.warning("""
        **📊 Using Simulated Environmental Data**
        - Analysis based on climate zone patterns
        - Realistic estimates for demonstration
        - Verify with local health authorities
        """)
    else:
        st.success("""
        **🌐 Using Real-Time Satellite Data**
        - Current Earth Engine observations
        - Live environmental monitoring
        - Maximum accuracy assessment
        """)

def show_enhanced_risk_interpretation(prediction, confidence, is_fallback):
    """Show enhanced risk interpretation with data source context"""
    st.subheader("🔍 Risk Interpretation")
    
    if prediction == "High":
        if is_fallback:
            st.error("""
            🚨 **HIGH RISK AREA** (Based on Climate Patterns)
            
            **⚠️ Important Note:** Using simulated data. Verify with local authorities.
            
            **Recommended Actions:**
            • Implement mosquito control
            • Public health awareness  
            • Regular monitoring
            • Coordinate with health services
            """)
        else:
            st.error("""
            🚨 **HIGH RISK AREA** (Based on Real-Time Data)
            
            **Immediate Actions:**
            • Activate control programs
            • Emergency awareness
            • Enhanced surveillance
            • Mobilize health workers
            """)
            
    elif prediction == "Medium":
        if is_fallback:
            st.warning("""
            ⚠️ **MEDIUM RISK AREA** (Based on Climate Patterns)
            
            **Note:** Using simulated environmental data.
            
            **Recommended:**
            • Seasonal surveillance
            • Basic prevention
            • Community awareness
            """)
        else:
            st.warning("""
            ⚠️ **MEDIUM RISK AREA** (Based on Real-Time Data)
            
            **Preventive Measures:**
            • Seasonal monitoring
            • Vector control
            • Community education
            """)
            
    else:
        if is_fallback:
            st.success("""
            ✅ **LOW RISK AREA** (Based on Climate Patterns)
            
            **Note:** Assessment uses simulated data.
            
            **Maintenance:**
            • Basic surveillance
            • Environmental monitoring
            • Health readiness
            """)
        else:
            st.success("""
            ✅ **LOW RISK AREA** (Based on Real-Time Data)
            
            **Current Status:**
            • Favorable conditions
            • Low transmission risk
            • Stable situation
            """)
    
    # Confidence and data source info
    col1, col2 = st.columns(2)
    with col1:
        source_type = "Simulated Data" if is_fallback else "Live Satellite Data"
        st.metric("Data Source", source_type)
    with col2:
        conf_label = "Est. Confidence" if is_fallback else "Confidence"
        st.metric(conf_label, f"{confidence:.1%}")

def show_prediction_charts(lat, lng, features, probabilities, prediction):
    """Show prediction charts in mobile-friendly layout"""
    st.subheader("📈 Analysis Charts")
    
    # Use tabs for better mobile organization
    tab1, tab2, tab3, tab4 = st.tabs(["🌧️ Rainfall", "🌡️ Temperature", "📊 Features", "🎯 Risk"])
    
    with tab1:
        historical_data = get_historical_data(lat, lng)
        if historical_data:
            rainfall_chart = create_rainfall_chart(historical_data)
            st.plotly_chart(rainfall_chart, use_container_width=True, key="rainfall_chart")
    
    with tab2:
        historical_data = get_historical_data(lat, lng)
        if historical_data:
            temp_chart = create_temperature_chart(historical_data)
            st.plotly_chart(temp_chart, use_container_width=True, key="temperature_chart")
    
    with tab3:
        feature_chart = create_feature_importance_chart(features)
        st.plotly_chart(feature_chart, use_container_width=True, key="feature_chart")
    
    with tab4:
        risk_chart = create_risk_chart(probabilities, prediction)
        st.plotly_chart(risk_chart, use_container_width=True, key="risk_chart")

def show_prediction_history():
    """Show user's prediction history with mobile optimization"""
    st.header("📋 Prediction History")
    
    predictions = get_user_predictions(st.session_state.user_id)
    
    if not predictions:
        st.info("No predictions yet. Go to the map and tap locations to make predictions!")
        return
    
    # Mobile-friendly data display
    history_data = []
    for pred in predictions:
        history_data.append({
            'Date': pred[7],
            'Latitude': f"{pred[2]:.4f}",
            'Longitude': f"{pred[3]:.4f}",
            'Prediction': pred[4],
            'Confidence': f"{pred[5]*100:.1f}%"
        })
    
    df = pd.DataFrame(history_data)
    
    # Use container width for better mobile display
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Statistics in responsive columns
    st.subheader("📊 Prediction Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Predictions", len(predictions))
    with col2:
        high_risk = len([p for p in predictions if p[4] == 'High'])
        st.metric("High Risk Areas", high_risk)
    with col3:
        avg_confidence = sum([p[5] for p in predictions]) / len(predictions)
        st.metric("Avg Confidence", f"{avg_confidence*100:.1f}%")
            
def show_account_info():
    """Show user account information with mobile optimization"""
    st.header("👤 Account Information")
    
    # Responsive columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Profile Details")
        st.info(f"""
        **Username:** {st.session_state.username}
        **User ID:** {st.session_state.user_id}
        """)
        
        # Prediction stats
        predictions = get_user_predictions(st.session_state.user_id)
        st.metric("Predictions Made", len(predictions))
    
    with col2:
        st.subheader("About FITSIS")
        st.markdown("""
        **Malaria Risk Prediction System**
        
        Uses machine learning to assess malaria risk based on:
        
        • Environmental factors
        • Geographic features  
        • Human factors
        
        **Data Sources:**
        - Google Earth Engine (live)
        - Climate patterns (fallback)
        - Global health data
        """)

if __name__ == "__main__":
    main()
