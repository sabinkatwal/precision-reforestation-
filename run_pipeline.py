"""
End-to-end execution and validation script for the Tree Prescriber pipeline.
Runs data building, model training, and performs test queries to verify system correctness.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to python path
sys.path.append(str(Path(__file__).resolve().parent))

def main():
    print("==================================================")
    print("STARTING TREE PRESCRIBER END-TO-END VALIDATION")
    print("==================================================")

    # Step 1: Run Dataset Builder
    print("\n--- RUNNING DATASET BUILDER ---")
    try:
        from ml_pipeline.build_dataset import build_dataset
        build_dataset()
        print("[SUCCESS] Dataset compiled successfully.")
    except Exception as e:
        print(f"[ERROR] Dataset builder failed: {e}")
        sys.exit(1)

    # Step 2: Run Model Training
    print("\n--- RUNNING MODEL TRAINING ---")
    try:
        from ml_pipeline.train import train_and_evaluate
        train_and_evaluate()
        print("[SUCCESS] Model trained and evaluated successfully.")
    except Exception as e:
        print(f"[ERROR] Model training failed: {e}")
        sys.exit(1)

    # Step 3: Run Inference Validation on test coordinates
    print("\n--- RUNNING INFERENCE VALIDATION ---")
    try:
        from ml_pipeline.predict import predict_species_suitability
        
        # Test coordinates 1: Lowland (Chitwan valley / Terai)
        # Lat: 27.55, Lon: 84.45 (Expected: Dalbergia sissoo / Sisau)
        lowland_lat, lowland_lon = 27.55, 84.45
        print(f"\nQuerying Lowland Coordinate (Lat: {lowland_lat}, Lon: {lowland_lon})...")
        lowland_res = predict_species_suitability(lowland_lat, lowland_lon)
        print(json.dumps(lowland_res, indent=2))
        
        # Test coordinates 2: Mid-Elevation Hills (Kathmandu / Bagmati)
        # Lat: 27.70, Lon: 85.30 (Expected: Pinus roxburghii / Salla)
        hill_lat, hill_lon = 27.70, 85.30
        print(f"\nQuerying Mid-Elevation Hills Coordinate (Lat: {hill_lat}, Lon: {hill_lon})...")
        hill_res = predict_species_suitability(hill_lat, hill_lon)
        print(json.dumps(hill_res, indent=2))
        
        # Validate output structure
        required_keys = ["location", "features", "recommendations"]
        for key in required_keys:
            if key not in lowland_res:
                raise ValueError(f"Missing required key in prediction output: {key}")
        
        print("\n[SUCCESS] Inference structures validated successfully.")
    except Exception as e:
        print(f"[ERROR] Inference validation failed: {e}")
        sys.exit(1)

    print("\n==================================================")
    print("ALL PIPELINE TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
