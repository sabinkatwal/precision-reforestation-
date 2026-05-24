"""Lightweight verification script for the ML pipeline.

This script performs a smoke test of the ML pipeline by ensuring a training
dataset exists (or creating a synthetic one), running training, and performing
an example inference. It is designed to be resilient when GBIF occurrence
files are not present by generating deterministic synthetic samples using the
`MockFeatureProvider`.
"""

import random
import pandas as pd
import numpy as np
import traceback
from pathlib import Path

from config import TRAINING_DATA_PATH, OCCURRENCE_FILES, NEPAL_BBOX
from build_dataset import build_dataset
from provider import MockFeatureProvider


def create_synthetic_dataset(n_samples: int = 60) -> None:
    print("Creating synthetic training dataset...")
    provider = MockFeatureProvider()

    # Derive species names from OCCURRENCE_FILES if available, otherwise fallback
    species_candidates = [f.parent.name for f in OCCURRENCE_FILES if f.exists()]
    if not species_candidates:
        species_candidates = ["Dalbergia sissoo", "Pinus roxburghii Sarg"]

    rows = []
    for i in range(n_samples):
        lat = random.uniform(NEPAL_BBOX["min_lat"], NEPAL_BBOX["max_lat"])
        lon = random.uniform(NEPAL_BBOX["min_lon"], NEPAL_BBOX["max_lon"])
        try:
            feats = provider.get_features(lat, lon)
        except Exception:
            # If provider rejects coordinate, nudge it slightly
            lat = np.clip(lat, NEPAL_BBOX["min_lat"], NEPAL_BBOX["max_lat"])
            lon = np.clip(lon, NEPAL_BBOX["min_lon"], NEPAL_BBOX["max_lon"])
            feats = provider.get_features(lat, lon)

        row = {
            "decimalLatitude": lat,
            "decimalLongitude": lon,
            **feats,
            "species": random.choice(species_candidates)
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(TRAINING_DATA_PATH, index=False)
    print(f"Synthetic dataset saved to: {TRAINING_DATA_PATH} (rows={len(df)})")


def verify_pipeline():
    print("=== ML PIPELINE VERIFICATION ===")

    # Step 1: Ensure training dataset exists
    if not TRAINING_DATA_PATH.exists() or TRAINING_DATA_PATH.stat().st_size == 0:
        # Attempt to build from occurrence files if they exist
        has_occurrences = any(p.exists() for p in OCCURRENCE_FILES)
        if has_occurrences:
            try:
                print("Building dataset from occurrence files...")
                build_dataset()
            except Exception as e:
                print(f"build_dataset() failed: {e}")
                traceback.print_exc()
        else:
            create_synthetic_dataset(n_samples=80)
    else:
        print(f"Found existing training dataset: {TRAINING_DATA_PATH}")

    # Quick check that dataset is readable
    try:
        df = pd.read_csv(TRAINING_DATA_PATH)
        print(f"Training dataset rows: {len(df)}, columns: {list(df.columns)[:8]}...")
    except Exception as e:
        print(f"Failed to read training dataset: {e}")
        raise

    # Step 2: Run training (this will train & export model artifacts)
    try:
        print("\nRunning training pipeline (train.py)... This may take time")
        from train import train_and_evaluate

        train_and_evaluate()
        print("Training completed successfully.")
    except Exception as e:
        print(f"Training failed: {e}")
        traceback.print_exc()
        return

    # Step 3: Run a sample inference using the trained artifacts
    try:
        print("\nRunning a sample inference using predict.py...")
        from predict import predict_species_suitability

        # Choose a sample coordinate (median of dataset)
        med_lat = float(df["decimalLatitude"].median())
        med_lon = float(df["decimalLongitude"].median())

        report = predict_species_suitability(med_lat, med_lon)
        print("Sample inference result (truncated):")
        # Print only the top recommendation for brevity
        top = report.get("recommendations", [])[0] if report.get("recommendations") else None
        print({"location": report.get("location"), "top_recommendation": top})
    except Exception as e:
        print(f"Sample inference failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    verify_pipeline()
