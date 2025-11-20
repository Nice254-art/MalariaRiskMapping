# app.py - Mobile Responsive FITSIS Malaria App
import streamlit as st
import os
import pandas as pd
from auth import login_user, register_user, logout_user, check_auth
from map_utils import create_interactive_map, extract_features_for_prediction, predict_malaria_risk
from charts import create_rainfall_chart, create_temperature_chart, create_risk_chart
from database import save_prediction, get_user_predictions
from streamlit_folium import st_folium

# Set page configuration for mobile responsiveness
st.set_page_config(
    page_title="FITSIS Malaria Risk Mapping",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Add custom CSS for mobile responsiveness
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main > div {
            padding-left: 1rem;
            padding-right: 1rem;
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
        
        /* Smaller text on mobile */
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        /* Adjust button sizes */
        .stButton > button {
            width: 100% !important;
            margin: 0.2rem 0;
        }
        
        /* Compact form fields */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
    }
    
    /* Tablet adjustments */
    @media (min-width: 769px) and (max-width: 1024px) {
        .folium-map {
            height: 400px !important;
        }
    }
    
    /* Desktop adjustments */
    @media (min-width: 1025px) {
        .folium-map {
            height: 500px !important;
        }
    }
    
    /* General mobile-friendly styles */
    .mobile-friendly {
        padding: 1rem;
    }
    
    .risk-card {
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .risk-low {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    
    .risk-medium {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    
    .risk-high {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    
    /* Compact data display for mobile */
    .compact-data {
        font-size: 0.9rem;
        line-height: 1.2;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Check authentication
    if not check_auth():
        return
    
    # Mobile-friendly header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🦟 FITSIS Malaria Risk Mapping")
        st.markdown("**Mobile-Friendly Malaria Risk Assessment System**")
    
    # Horizontal rule for separation
    st.markdown("---")
    
    # Main content area with responsive layout
    st.header("📍 Select Location for Risk Assessment")
    
    # Map section - responsive
    st.subheader("Interactive Map")
    st.markdown("Tap on the map below to select a location for malaria risk analysis")
    
    # Create map with responsive height
    m = create_interactive_map()
    
    # Display map - this will be responsive based on our CSS
    map_data = st_folium(m, width=None, height=400)  # Height will be overridden by CSS
    
    # Location input section - responsive columns
    st.subheader("Location Details")
    
    # Use columns that stack on mobile
    col1, col2 = st.columns(2)
    
    with col1:
        lat = st.number_input(
            "Latitude", 
            min_value=-90.0, 
            max_value=90.0, 
            value=0.0,
            help="Enter latitude or click on map"
        )
        
    with col2:
        lon = st.number_input(
            "Longitude", 
            min_value=-180.0, 
            max_value=180.0, 
            value=20.0,
            help="Enter longitude or click on map"
        )
    
    # Update coordinates if user clicked on map
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"📍 Location selected: {lat:.4f}, {lon:.4f}")
    
    # Analysis date - full width on mobile
    analysis_date = st.date_input(
        "Analysis Date",
        value=pd.to_datetime("today"),
        help="Select date for malaria risk assessment"
    )
    
    # Risk assessment button - full width on mobile
    st.markdown("---")
    st.subheader("🦟 Malaria Risk Analysis")
    
    if st.button("🔍 Assess Malaria Risk", use_container_width=True):
        with st.spinner("Analyzing environmental factors..."):
            # Extract features
            features = extract_features_for_prediction(lat, lon)
            
            if features:
                # Make prediction
                prediction, confidence, probabilities = predict_malaria_risk(features)
                
                # Display risk results in mobile-friendly cards
                st.markdown("### 📊 Risk Assessment Results")
                
                # Risk level card
                risk_class = f"risk-{prediction.lower()}"
                st.markdown(f"""
                <div class="risk-card {risk_class}">
                    <h4>Malaria Risk Level: {prediction}</h4>
                    <p><strong>Confidence:</strong> {confidence:.1%}</p>
                    <p><strong>Location:</strong> {lat:.4f}, {lon:.4f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Risk factors in compact format
                st.markdown("### 🔍 Environmental Risk Factors")
                
                # Use columns that stack on mobile
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("🌧️ Rainfall", f"{features.get('rainfall_12mo', 0):.1f} mm")
                    st.metric("🌡️ Temperature", f"{features.get('temp_mean_c', 0):.1f}°C")
                    st.metric("🌿 NDVI", f"{features.get('ndvi_mean', 0):.3f}")
                
                with col2:
                    st.metric("👥 Population", f"{features.get('pop_density', 0):.0f}/km²")
                    st.metric("🏔️ Elevation", f"{features.get('elevation', 0):.0f} m")
                    st.metric("💧 Water Coverage", f"{features.get('water_coverage', 0):.1f}%")
                
                # Charts section - responsive
                st.markdown("### 📈 Historical Trends")
                
                # Get historical data
                from map_utils import get_historical_data
                historical_data = get_historical_data(lat, lon)
                
                # Display charts in responsive layout
                tab1, tab2, tab3 = st.tabs(["🌧️ Rainfall", "🌡️ Temperature", "📊 Risk Distribution"])
                
                with tab1:
                    st.plotly_chart(create_rainfall_chart(historical_data), use_container_width=True)
                
                with tab2:
                    st.plotly_chart(create_temperature_chart(historical_data), use_container_width=True)
                
                with tab3:
                    st.plotly_chart(create_risk_chart(probabilities, prediction), use_container_width=True)
                
                # Save prediction
                if st.session_state.get('user'):
                    save_prediction(
                        st.session_state.user['id'],
                        lat, lon,
                        prediction,
                        confidence,
                        features
                    )
                    st.success("✅ Prediction saved to your history")
    
    # User predictions history - mobile optimized
    st.markdown("---")
    st.subheader("📋 Your Prediction History")
    
    if st.session_state.get('user'):
        user_predictions = get_user_predictions(st.session_state.user['id'])
        
        if user_predictions:
            # Display in a mobile-friendly table
            df = pd.DataFrame(user_predictions)
            st.dataframe(
                df[['latitude', 'longitude', 'prediction', 'confidence', 'created_at']],
                use_container_width=True
            )
        else:
            st.info("No predictions yet. Analyze a location to see your history here.")
    
    # Footer with mobile-friendly layout
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    
    with footer_col1:
        st.markdown("**FITSIS**")
        st.markdown("Malaria Risk Mapping")
    
    with footer_col2:
        st.markdown("**Need Help?**")
        st.markdown("📧 Contact Support")
    
    with footer_col3:
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()

if __name__ == "__main__":
    main()
