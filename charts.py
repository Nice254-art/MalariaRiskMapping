# charts.py
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_rainfall_chart(historical_data):
    """Create rainfall trend chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_data['years'],
        y=historical_data['rainfall'],
        mode='lines+markers',
        name='Annual Rainfall',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Annual Rainfall Trend (Last 5 Years)',
        xaxis_title='Year',
        yaxis_title='Rainfall (mm)',
        template='plotly_white'
    )
    
    return fig

def create_temperature_chart(historical_data):
    """Create temperature trend chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_data['years'],
        y=historical_data['temperature'],
        mode='lines+markers',
        name='Average Temperature',
        line=dict(color='red', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Annual Temperature Trend (Last 5 Years)',
        xaxis_title='Year',
        yaxis_title='Temperature (°C)',
        template='plotly_white'
    )
    
    return fig

def create_feature_importance_chart(features):
    """Create feature importance visualization"""
    feature_names = list(features.keys())
    feature_values = list(features.values())
    
    # Create readable feature names
    readable_names = {
        'rainfall_12mo': 'Rainfall (mm)',
        'temp_mean_c': 'Temperature (°C)',
        'ndvi_mean': 'Vegetation (NDVI)',
        'pop_density': 'Population Density',
        'elevation': 'Elevation (m)',
        'water_coverage': 'Water Coverage (%)'
    }
    
    readable_feature_names = [readable_names.get(name, name) for name in feature_names]
    
    df = pd.DataFrame({
        'Feature': readable_feature_names,
        'Value': feature_values
    })
    
    fig = px.bar(df, x='Value', y='Feature', orientation='h',
                 title='Environmental Features at Selected Location',
                 color='Value', color_continuous_scale='Viridis')
    
    fig.update_layout(template='plotly_white')
    
    return fig

def create_prediction_gauge(prediction, confidence):
    """Create a gauge chart for prediction confidence"""
    if prediction == "High":
        color = "red"
        risk_level = "High Risk"
    elif prediction == "Medium":
        color = "orange" 
        risk_level = "Medium Risk"
    else:
        color = "green"
        risk_level = "Low Risk"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Confidence: {risk_level}"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 33], 'color': "lightgray"},
                {'range': [33, 66], 'color': "gray"},
                {'range': [66, 100], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': confidence * 100
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig