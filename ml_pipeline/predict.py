"""
Inference pipeline for the Tree Prescriber system.
Accepts coordinates, extracts environmental features from a FeatureProvider,
runs the trained ML model, and returns ranked species suggestions with explanations.
"""

import sys
import json
import argparse
import pandas as pd
import joblib
from pathlib import Path

# Add parent directory to sys.path to allow running directly from CLI
sys.path.append(str(Path(__file__).resolve().parent))

from config import MODEL_PATH, ENCODERS_PATH
from provider import FeatureProvider, MockFeatureProvider
from explain import generate_explanations


def predict_species_suitability(lat: float, lon: float, provider: FeatureProvider = None) -> dict:
    """
    Predicts tree species suitability for a given coordinate.
    
    Args:
        lat (float): Latitude coordinate.
        lon (float): Longitude coordinate.
        provider (FeatureProvider, optional): Feature provider instance. Defaults to MockFeatureProvider.
        
    Returns:
        dict: Recommendation report conforming to requirements.
    """
    # 1. Instantiate FeatureProvider if not provided (defaults to Mock)
    if provider is None:
        provider = MockFeatureProvider()

    # 2. Extract environmental features at coordinates
    # This acts as our deterministic function: F(lat, lon) -> environmental features
    try:
        narc_features = provider.get_features(lat, lon)
    except Exception as e:
        raise ValueError(f"Feature extraction failed at coordinate ({lat}, {lon}): {e}")

    # 3. Load Trained Model and Encoders
    if not MODEL_PATH.exists() or not ENCODERS_PATH.exists():
        raise FileNotFoundError(
            f"Trained model artifacts missing. Please train the model first by running train.py."
        )

    pipeline = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODERS_PATH)

    feature_engineer = encoders["feature_engineer"]
    label_encoder = encoders["label_encoder"]

    # 4. Construct input row for transformation
    input_df = pd.DataFrame([{
        "latitude": lat,
        "longitude": lon,
        **narc_features
    }])

    # 5. Transform through the Feature Engineer
    # This applies nutrient ratios, USDA texture, elevation bands, and spatial clustering
    input_engineered = feature_engineer.transform(input_df)

    # 6. Model Prediction Probabilities
    # Probabilities serve as the suitability/confidence scores
    probs = pipeline.predict_proba(input_engineered)[0]
    classes = label_encoder.classes_

    # 7. Compile and Rank Recommendations
    recommendations = []
    for i, score in enumerate(probs):
        species_name = classes[i]
        
        # Generate explanations using SHAP and ecological rules
        reasons = generate_explanations(pipeline, input_engineered, species_name, float(score), label_encoder)
        
        recommendations.append({
            "species": species_name,
            "score": round(float(score), 4),
            "reasons": reasons
        })

    # Sort recommendations descending by score
    recommendations = sorted(recommendations, key=lambda x: x["score"], reverse=True)

    # 8. Return formatted output structure
    return {
        "location": {
            "latitude": lat,
            "longitude": lon
        },
        "features": narc_features,
        "recommendations": recommendations
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tree Prescriber Inference CLI")
    parser.add_argument("--lat", type=float, required=True, help="Latitude (e.g. 27.7)")
    parser.add_argument("--lon", type=float, required=True, help="Longitude (e.g. 85.3)")
    
    args = parser.parse_args()

    try:
        result = predict_species_suitability(args.lat, args.lon)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
