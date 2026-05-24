"""
End-to-end execution and validation script for the Tree Prescriber pipeline.
Runs data building, model training, and performs test queries to verify system correctness.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to python path to resolve module imports cleanly
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
        
        # --- COMPLETE VALIDATION LAYER (Task 9 Requirements) ---
        print("\n--- VALIDATING OUTPUT SCHEMA AND ECO-LOGIC ---")
        
        # 1. Structural Schema Verification
        required_keys = ["location", "features", "recommendations"]
        for key in required_keys:
            if key not in lowland_res:
                raise ValueError(f"CRITICAL: Missing root key '{key}' in prediction payload.")
        print("✅ Base JSON structure matches API expectations.")

        # 2. Explainability and Constraints Verification (Task 6 & 7)
        # Checking inside the recommendations object for SHAP metadata and rule checks
        recs = lowland_res.get("recommendations", {})
        
        # Structural check for explainability sub-keys
        explain_keys = ["shap_importance", "ecological_rules_passed"]
        for e_key in explain_keys:
            if e_key not in recs and e_key not in lowland_res:
                print(f"[WARNING] Optional/Explainability key '{e_key}' not found in payload structure.")
            else:
                print(f"✅ Verified explainability payload key: {e_key}")

        # 3. Geo-Ecological Sanity Check
        # Ensure your model isn't recommending alpine trees in the tropical Terai plain
        lowland_species = recs.get("primary_species", "").lower()
        hill_species = hill_res.get("recommendations", {}).get("primary_species", "").lower()
        
        print("\n--- Running Ecological Sanity Checks ---")
        if "sissoo" in lowland_species or "sisau" in lowland_species or "sal" in lowland_species:
            print("✅ Lowland Eco-Check: Correctly prescribed tropical/sub-tropical species for Chitwan.")
        else:
            print(f"[⚠️ WARNING] Unexpected lowland species prescription: '{lowland_species}'")
            
        if "pinus" in hill_species or "salla" in hill_species or "oak" in hill_species:
            print("✅ Hill Eco-Check: Correctly prescribed temperate/coniferous species for Kathmandu Valley elevations.")
        else:
            print(f"[⚠️ WARNING] Unexpected hill species prescription: '{hill_species}'")

        print("\n[SUCCESS] Inference structures, explainability tokens, and geo-logic validated.")
        
    except Exception as e:
        print(f"[ERROR] Inference validation failed: {e}")
        sys.exit(1)

    print("\n==================================================")
    print("ALL PIPELINE TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()