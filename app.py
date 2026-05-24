from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="The Tree Prescription API")

# Load model on startup
try:
    model = joblib.load('tree_model.joblib')
except:
    model = None

class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    elevation: float
    ndvi: float
    slope: float
    aspect: float

@app.get("/")
def read_root():
    return {"status": "The Tree Prescription Engine is Active"}

@app.post("/predict")
def predict_species(request: PredictionRequest):
    if model is None:
        return {"error": "Model not found. Please train the model first."}
    
    # Prepare features for inference
    features = np.array([[
        request.latitude, 
        request.longitude, 
        request.elevation, 
        request.ndvi, 
        request.slope, 
        request.aspect
    ]])
    
    # Get probabilities
    # Classes: [0: Unsuitable, 1: Salla, 2: Sisau, 3: Lali Gurans]
    probs = model.predict_proba(features)[0]
    
    # Map classes to names
    # Note: Depending on the training data, some classes might not exist if data is sparse, 
    # but with our 1000 samples mock data, they should all be there.
    # We ensure indices match the trained model classes.
    class_map = {0: "Unsuitable", 1: "Salla", 2: "Sisau", 3: "Lali Gurans"}
    
    results = {}
    for i, prob in enumerate(probs):
        species_name = class_map.get(i, f"Unknown_{i}")
        results[species_name] = round(float(prob), 4)
    
    return {
        "input": request.dict(),
        "prescriptions": results,
        "recommended_species": class_map.get(int(model.predict(features)[0]), "None")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
