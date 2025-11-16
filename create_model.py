# create_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import os

print("🔄 Creating malaria prediction model...")

# Create models directory
os.makedirs('models', exist_ok=True)

def create_sample_training_data():
    """Create realistic training data for malaria prediction"""
    np.random.seed(42)
    n_samples = 200
    
    # Realistic ranges based on malaria epidemiology
    data = {
        'rainfall_12mo': np.random.uniform(200, 2500, n_samples),  # mm/year
        'temp_mean_c': np.random.uniform(18, 32, n_samples),       # °C (optimal for mosquitoes: 20-30°C)
        'ndvi_mean': np.random.uniform(0.1, 0.8, n_samples),       # vegetation index
        'pop_density': np.random.uniform(0, 1000, n_samples),      # people/km²
        'elevation': np.random.uniform(0, 2500, n_samples),        # meters
        'water_coverage': np.random.uniform(0, 40, n_samples)      # %
    }
    
    df = pd.DataFrame(data)
    
    # Create realistic malaria risk based on known factors
    # High risk: warm temperatures (25-30°C), moderate-high rainfall, some population
    risk_scores = (
        (df['temp_mean_c'] - 25).abs() / 10 +          # Optimal around 25°C
        df['rainfall_12mo'] / 1500 +                   # Moderate rainfall good
        np.minimum(df['pop_density'] / 200, 1) +       # Some population needed
        df['water_coverage'] / 20 +                    # Some water bodies
        (2000 - df['elevation']) / 2000                # Lower elevation better
    )
    
    # Convert to categories with realistic distribution
    df['malaria_risk'] = pd.cut(risk_scores, 
                               bins=[0, 1.2, 2.0, 3], 
                               labels=['Low', 'Medium', 'High'])
    
    return df

# Create training data
df = create_sample_training_data()
print(f"✅ Created training data with {len(df)} samples")

# Show distribution
print("\n📊 Malaria Risk Distribution:")
print(df['malaria_risk'].value_counts())

# Prepare features and target
features = ['rainfall_12mo', 'temp_mean_c', 'ndvi_mean', 'pop_density', 'elevation', 'water_coverage']
X = df[features]
y = df['malaria_risk']

# Create and train model
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(
        n_estimators=100, 
        random_state=42, 
        class_weight='balanced',
        max_depth=10,
        min_samples_split=5
    ))
])

pipeline.fit(X, y)
print("✅ Model trained successfully")

# Save model
joblib.dump(pipeline, 'models/malaria_model_expanded.pkl')
print("✅ Model saved as 'models/malaria_model_expanded.pkl'")

# Create feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': pipeline.named_steps['classifier'].feature_importances_
}).sort_values('importance', ascending=False)

feature_importance.to_csv('models/feature_importance.csv', index=False)
print("✅ Feature importance saved")

# Test the model
print("\n🧪 Testing model with sample locations:")

# High risk example (warm, moderate rain, some population)
high_risk_example = [[1200, 28, 0.6, 150, 200, 15]]
prediction = pipeline.predict(high_risk_example)
probability = pipeline.predict_proba(high_risk_example)
print(f"📍 High-risk area: {prediction[0]} (confidence: {max(probability[0]):.2f})")

# Low risk example (cool, low population, high elevation)
low_risk_example = [[800, 18, 0.3, 10, 1500, 2]]
prediction = pipeline.predict(low_risk_example)
probability = pipeline.predict_proba(low_risk_example)
print(f"📍 Low-risk area: {prediction[0]} (confidence: {max(probability[0]):.2f})")

print("\n🎉 Model creation complete! Ready for Streamlit app.")