

# 🌍 **Malaria Risk Mapping & Prediction System**

A machine-learning–powered system for **risk assessment**, **early warning**, and **geospatial mapping** of malaria across different ecological zones. The platform combines **environmental**, **climatic**, and **geographical** indicators to generate accurate risk predictions that support public health planning and rapid interventions.

---

## 🚀 **Live Demo**

Experience the system in action! Our interactive web application allows you to explore malaria risk predictions and generate maps in real-time.

🔗 **Live Demo Link:** [https://malaria2.streamlit.app/](https://malaria2.streamlit.app/)

*   **Visualize Risk Maps:** See high-risk areas highlighted on an interactive map.
*   **Run Predictions:** Input environmental data to get instant risk scores.
*   **Explore Features:** Understand how different factors like rainfall and temperature influence the model's output.

---

## 📖 **Overview**

The **Malaria Risk Mapping and Prediction System** uses a multivariate model trained on historical malaria incidence data and environmental variables.
It provides:

* Real-time malaria risk predictions
* Automated feature validation and data imputation
* GIS-ready geospatial risk layers
* An early-warning system for outbreak detection
* District-level insights for health authorities

---

## 🗃️ **Database & Model**

The accuracy of our predictions is built on a foundation of robust, multi-source data.

### **Data Sources**
Our model is trained on and ingests data from the following primary sources:

*   **Historical Malaria Incidence:** Lab-confirmed case data from health facilities and national surveillance systems, aggregated by district and season.
*   **Climate & Weather:** Time-series data on precipitation and land surface temperature from satellite sources (e.g., CHIRPS, MODIS).
*   **Environmental Metrics:** Vegetation indices (NDVI) and water body data derived from satellite imagery (e.g., Landsat, Sentinel).
*   **Topographical Data:** Global elevation data (e.g., SRTM) to account for altitude-based mosquito habitat constraints.
*   **Population Data:** Gridded population density estimates from sources like WorldPop.

### **Model Training**
The predictive model is an **ensemble machine learning model** (e.g., Random Forest or Gradient Boosting) trained on the relationship between the input features (see below) and historical malaria incidence rates. The model is periodically retrained with new outbreak data to maintain its accuracy over time.

---

## 🎯 **Key Features**

* **🔍 Multi-Factor Risk Analysis**
  Evaluates 6 core environmental and climatic indicators.

* **⚡ Real-Time Prediction**
  Instant malaria risk score (0–1) + probability distribution.

* **🗺️ Geospatial Mapping**
  Visualizes risk distribution across geographic space.

* **✔ Feature Validation Engine**
  Detects missing values, unrealistic ranges, and data gaps.

* **🚨 Early Warning System**
  Flags high-risk areas using thresholds and probability signals.

---

## 📊 **Input Features**

| Feature            | Description                        | Unit       | Expected Range | Importance                          |
| ------------------ | ---------------------------------- | ---------- | -------------- | ----------------------------------- |
| **rainfall_12mo**  | Total precipitation over 12 months | mm         | 0–2000+        | ⭐ High — breeding sites             |
| **temp_mean_c**    | Average temperature                | °C         | 10–35          | ⭐ Critical — parasite development   |
| **ndvl_mean**      | NDVI vegetation index              | Ratio      | 0–1            | Medium — habitat suitability        |
| **pop_density**    | Population density                 | people/km² | 0–10,000+      | ⭐ High — transmission potential     |
| **elevation**      | Altitude above sea level           | m          | –100 to 5000   | Medium — mosquito species range     |
| **water_coverage** | % water bodies                     | %          | 0–100          | ⭐ High — breeding site availability |

---

## 🚀 **Installation**

### **Prerequisites**

* Python **3.8+**
* pip
* API keys for geographical/weather/satellite data (optional)

### **Install Dependencies**

```bash
pip install pandas numpy scikit-learn matplotlib seaborn geopandas rasterio requests streamlit
```

### **Clone the Repository**

```bash
git clone https://github.com/your-org/malaria-risk-mapping.git
cd malaria-risk-mapping
```

### **Environment Variables**

Create a `.env` file:

```
WEATHER_API_KEY=your_key_here
ELEVATION_API_KEY=your_key_here
SATELLITE_DATA_KEY=your_key_here
```

---

## 🏗️ **System Architecture**

### **🔄 Data Flow**

```
Data Sources → Feature Extraction → Validation → Model Prediction → Risk Output
    ↓                ↓                 ↓              ↓                ↓
 Satellite       rainfall_12mo     Zero-value      ML Model       Low / Medium / High
 Weather APIs    temp_mean_c       checks          Inference      Risk Classification
 Census Data     pop_density       Imputation
```

### **Core Components**

#### **1. Data Extraction Module**

* Fetches satellite, weather, and demographic data
* Handles API rate limits and failures
* Performs coordinate-based lookups

#### **2. Feature Validation Engine**

* Detects zero or missing values
* Performs geospatial context imputation
* Ensures biological plausibility of input ranges

#### **3. Prediction Model**

* Ensemble ML model trained on incidence datasets
* Produces probability scores + categorical risk
* Updated periodically using new outbreak data

---

## 🛠️ **Usage**

### **Basic Implementation**

```python
from malaria_predictor import MalariaRiskPredictor

predictor = MalariaRiskPredictor()

features = {
    'rainfall_12mo': 968.59,
    'temp_mean_c': 27.5,
    'ndvl_mean': 0.68,
    'pop_density': 245.0,
    'elevation': 418.09,
    'water_coverage': 3.2
}

risk_level, probability = predictor.predict(features)
print(f"Malaria Risk: {risk_level} ({probability:.2%})")
```

### **Zero-Value Handling**

```python
# Automatically fill missing values
features = predictor.impute_missing_values(features)

# Validate before prediction
if predictor.validate_features(features):
    result = predictor.predict(features)
else:
    print("Feature validation failed — check input data.")
```

---

## 🐛 **Troubleshooting**

### **Zero-Value Feature Errors**

**Cause:** API returned missing or zero-value environmental data
**Solutions:**

#### 1. Check API responsiveness

```python
predictor.test_data_sources()
```

#### 2. Apply defaults (based on regional ecology)

```python
features = {
    'temp_mean_c': 25.0 if temp == 0 else temp,
    'ndvl_mean': 0.6 if ndvl == 0 else ndvl,
    'pop_density': 100.0 if pop == 0 else pop,
    'water_coverage': 2.5 if water == 0 else water
}
```

#### 3. Validate coordinates & rate limits

* Ensure lat/lon are in correct decimal format
* Check API quota
* Ensure network connectivity

---

## 📈 **Output Interpretation**

### **Risk Categories**

| Category        | Score Range | Meaning                           |
| --------------- | ----------- | --------------------------------- |
| **Low Risk**    | 0.0–0.3     | Minimal intervention needed       |
| **Medium Risk** | 0.3–0.7     | Enhanced surveillance recommended |
| **High Risk**   | 0.7–1.0     | Immediate intervention required   |

### **Confidence Indicators**

* Data quality score
* Feature completeness
* Temporal freshness of data
* Interpolation confidence

---

## 🔧 **Configuration**

Example configuration:

```python
config = {
    'risk_thresholds': {'low': 0.3, 'medium': 0.7, 'high': 1.0},
    'imputation_strategy': 'geographical_context',
    'minimum_data_quality': 0.8,
    'update_frequency': 'weekly'
}
```

---

## 🤝 **Contributing**

1. Submit issues for data or model inconsistencies
2. Follow feature validation guidelines
3. Test with diverse environmental zones
4. Document newly integrated data sources

---

## 📄 **License**

Licensed under the **MIT License**.
See the `LICENSE` file for details.

---

## 🆘 **Support**

For help:

* Review the troubleshooting section
* Validate API keys and data sources
* Open a GitHub issue with:
  * Coordinates used
  * Full error traceback
  * Raw feature values

---
