# charts.py - Mobile Responsive + Enhanced Features
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_mobile_config():
    """Configuration for mobile-responsive charts"""
    return {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
        'responsive': True
    }

def create_rainfall_chart(historical_data):
    """Create mobile-friendly rainfall chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_data['years'],
        y=historical_data['rainfall'],
        mode='lines+markers',
        name='Annual Rainfall',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='🌧️ Annual Rainfall Trend (Last 5 Years)',
        xaxis_title='Year',
        yaxis_title='Rainfall (mm)',
        template='plotly_white',
        height=300,  # Mobile-friendly height
        margin=dict(l=50, r=20, t=50, b=50),  # Better mobile margins
        font=dict(size=12)
    )
    
    return fig

def create_temperature_chart(historical_data):
    """Create mobile-friendly temperature chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_data['years'],
        y=historical_data['temperature'],
        mode='lines+markers',
        name='Average Temperature',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='🌡️ Annual Temperature Trend (Last 5 Years)',
        xaxis_title='Year',
        yaxis_title='Temperature (°C)',
        template='plotly_white',
        height=300,
        margin=dict(l=50, r=20, t=50, b=50),
        font=dict(size=12)
    )
    
    return fig

def create_feature_importance_chart(features):
    """Create mobile-friendly feature importance visualization"""
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
                 title='📊 Environmental Features at Location',
                 color='Value', 
                 color_continuous_scale='Viridis')
    
    fig.update_layout(
        template='plotly_white',
        height=350,  # Slightly taller for horizontal bars
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(size=11)  # Slightly smaller font for horizontal labels
    )
    
    return fig

def create_prediction_gauge(prediction, confidence):
    """Create a mobile-friendly gauge chart for prediction confidence"""
    if prediction == "High":
        color = "red"
        risk_level = "High Risk"
        gauge_color = "#dc3545"
    elif prediction == "Medium":
        color = "orange" 
        risk_level = "Medium Risk"
        gauge_color = "#ffc107"
    else:
        color = "green"
        risk_level = "Low Risk"
        gauge_color = "#28a745"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"🦟 {risk_level}", 'font': {'size': 16}},
        number = {'suffix': "%", 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': gauge_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 33], 'color': '#d4edda'},  # Light green
                {'range': [33, 66], 'color': '#fff3cd'},  # Light yellow
                {'range': [66, 100], 'color': '#f8d7da'}  # Light red
            ],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.8,
                'value': confidence * 100
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=30, r=30, t=50, b=20),
        font=dict(size=12)
    )
    
    return fig

def create_risk_chart(probabilities, prediction):
    """Create mobile-friendly risk probability chart"""
    risk_levels = ['Low', 'Medium', 'High']
    colors = ['#28a745', '#ffc107', '#dc3545']
    
    # Highlight the predicted risk level
    highlight_index = risk_levels.index(prediction)
    
    fig = go.Figure(data=[
        go.Bar(
            x=risk_levels,
            y=probabilities,
            marker_color=colors,
            text=[f'{p:.1%}' for p in probabilities],
            textposition='auto',
            marker_line=dict(
                color=['black' if i == highlight_index else 'white' for i in range(len(risk_levels))],
                width=2
            )
        )
    ])
    
    fig.update_layout(
        title='📈 Malaria Risk Probability Distribution',
        xaxis_title='Risk Level',
        yaxis_title='Probability',
        height=300,
        margin=dict(l=50, r=20, t=50, b=50),
        font=dict(size=12),
        showlegend=False
    )
    
    return fig

def create_comparison_chart(current_features, avg_features=None):
    """Create comparison chart between current location and regional averages"""
    features_display = {
        'rainfall_12mo': 'Rainfall',
        'temp_mean_c': 'Temperature', 
        'ndvi_mean': 'Vegetation',
        'pop_density': 'Population',
        'elevation': 'Elevation',
        'water_coverage': 'Water Cover'
    }
    
    # If no averages provided, create some for demonstration
    if avg_features is None:
        avg_features = {
            'rainfall_12mo': 850,
            'temp_mean_c': 26,
            'ndvi_mean': 0.4,
            'pop_density': 45,
            'elevation': 350,
            'water_coverage': 12
        }
    
    features_list = list(features_display.keys())
    current_values = [current_features.get(f, 0) for f in features_list]
    avg_values = [avg_features.get(f, 0) for f in features_list]
    feature_labels = [features_display[f] for f in features_list]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Current Location',
        x=feature_labels,
        y=current_values,
        marker_color='#1f77b4'
    ))
    
    fig.add_trace(go.Bar(
        name='Regional Average',
        x=feature_labels,
        y=avg_values,
        marker_color='#ff7f0e'
    ))
    
    fig.update_layout(
        title='📋 Feature Comparison: Current vs Regional Average',
        xaxis_title='Environmental Factors',
        yaxis_title='Values',
        barmode='group',
        height=350,
        margin=dict(l=50, r=20, t=50, b=80),  # Extra bottom margin for rotated labels
        font=dict(size=11),
        xaxis_tickangle=-45  # Rotate labels for better mobile display
    )
    
    return fig
