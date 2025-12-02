from fastapi.testclient import TestClient
from api import app
import os

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "service": "Malaria Risk Mapping API"}

def test_prediction_endpoint_structure():
    # We expect this to fail GEE auth if no creds, but return fallback data
    # or at least a valid structure.
    response = client.post("/api/malaria-risk", json={"lat": 0.0, "lng": 20.0})
    assert response.status_code == 200
    data = response.json()
    assert "risk_level" in data
    assert "features" in data
    assert "data_source" in data
    
    # Check if fallback is working (since we likely don't have real creds in this env)
    if data["data_source"] == "Simulated (Fallback)":
        print("Verified: API correctly falls back to simulated data when GEE is missing.")
    else:
        print(f"Verified: API returned data from {data['data_source']}")

if __name__ == "__main__":
    test_read_root()
    test_prediction_endpoint_structure()
    print("All tests passed!")
