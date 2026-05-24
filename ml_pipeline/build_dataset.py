"""
Dataset builder for the Tree Prescriber machine learning pipeline.
Reads real GBIF occurrences, cleans coordinates, filters by uncertainty,
and joins deterministic features from the FeatureProvider.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to sys.path to allow running from any folder
sys.path.append(str(Path(__file__).resolve().parent))

from config import NEPAL_BBOX, OCCURRENCE_FILES, TRAINING_DATA_PATH, USE_NARC_PROVIDER
from provider import MockFeatureProvider, NARCFeatureProvider

def create_feature_provider():
    if USE_NARC_PROVIDER:
        print("Using NARCFeatureProvider for environmental feature lookup.")
        return NARCFeatureProvider()
    print("Using MockFeatureProvider for environmental feature lookup.")
    return MockFeatureProvider()


def load_and_clean_occurrences() -> pd.DataFrame:
    """
    Loads raw occurrences, applies geospatial cleaning and quality filtering,
    and returns a combined DataFrame.
    """
    combined_records = []

    for file_path in OCCURRENCE_FILES:
        if not file_path.exists():
            print(f"Warning: Occurrence file not found at {file_path}")
            continue
        
        print(f"Reading occurrence data from {file_path.parent.name}...")
        try:
            # GBIF files are tab-separated
            df = pd.read_csv(file_path, sep="\t", low_memory=False)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        print(f"  Loaded {len(df)} raw records.")

        # 1. Coordinate Validation (not null, numeric, within Nepal bounds)
        lat_col = "decimalLatitude"
        lon_col = "decimalLongitude"
        
        if lat_col not in df.columns or lon_col not in df.columns:
            print(f"  Error: Bounding coordinate columns missing in {file_path}")
            continue

        # Convert to numeric, coerce errors to NaN
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
        
        # Drop rows with missing coordinates
        df = df.dropna(subset=[lat_col, lon_col])

        # Filter points within Nepal Bounding Box
        in_nepal = (
            (df[lat_col] >= NEPAL_BBOX["min_lat"]) & (df[lat_col] <= NEPAL_BBOX["max_lat"]) &
            (df[lon_col] >= NEPAL_BBOX["min_lon"]) & (df[lon_col] <= NEPAL_BBOX["max_lon"])
        )
        df = df[in_nepal]
        print(f"  Records within Nepal bounds: {len(df)}")

        # 2. Geospatial Issues Filter
        # Remove records where GBIF has identified spatial issues
        if "hasGeospatialIssues" in df.columns:
            df = df[df["hasGeospatialIssues"] != True]
            print(f"  Records passing geospatial issue check: {len(df)}")

        # 3. Coordinate Uncertainty Filter
        # Remove records with uncertainty > 1000m to avoid training on fuzzy spatial locations
        if "coordinateUncertaintyInMeters" in df.columns:
            # Replace NaNs with a default reasonable uncertainty (e.g., 100m) to keep records
            uncertainty = df["coordinateUncertaintyInMeters"].fillna(100.0)
            df = df[uncertainty <= 1000.0]
            print(f"  Records passing uncertainty filter (<=1000m): {len(df)}")

        # 4. Species column extraction
        if "species" not in df.columns:
            print(f"  Error: 'species' label column missing in {file_path}")
            continue

        # Extract only columns of interest
        cleaned_df = df[[lat_col, lon_col, "species"]].copy()
        
        # Strip trailing/leading spaces from species names
        cleaned_df["species"] = cleaned_df["species"].str.strip()
        cleaned_df = cleaned_df.dropna(subset=["species"])
        
        combined_records.append(cleaned_df)

    if not combined_records:
        raise ValueError("No occurrence records found or loaded after cleaning!")

    full_df = pd.concat(combined_records, ignore_index=True)

    # 5. Coordinate Deduplication (for the same species)
    # If the exact same coordinate and species is recorded, drop the duplicate
    initial_len = len(full_df)
    full_df = full_df.drop_duplicates(subset=["decimalLatitude", "decimalLongitude", "species"])
    print(f"Deduplicated combined records from {initial_len} to {len(full_df)}")

    return full_df

def build_dataset():
    """
    Main function to run occurrence cleaning and join environmental features.
    """
    print("=== STEP 1 & 2: LOADING AND CLEANING OCCURRENCES ===")
    occurrences = load_and_clean_occurrences()

    print("\n=== STEP 3: JOINING ENVIRONMENTAL FEATURES ===")
    provider = create_feature_provider()
    
    dataset_rows = []
    
    # Iterate through occurrence points and extract features
    for idx, row in occurrences.iterrows():
        lat = row["decimalLatitude"]
        lon = row["decimalLongitude"]
        species = row["species"]
        
        try:
            # Query MockFeatureProvider for coordinates
            features = provider.get_features(lat, lon)
            
            # Combine coordinates, features, and target label
            sample = {
                "latitude": lat,
                "longitude": lon,
                **features,
                "species": species
            }
            dataset_rows.append(sample)
        except Exception as e:
            print(f"Error querying features at ({lat}, {lon}) for {species}: {e}")

    # Convert to DataFrame
    dataset_df = pd.DataFrame(dataset_rows)
    print(f"Successfully compiled {len(dataset_df)} samples.")
    
    # Display species distributions
    print("\nFinal Species Distribution in Dataset:")
    print(dataset_df["species"].value_counts())

    # Save to CSV
    dataset_df.to_csv(TRAINING_DATA_PATH, index=False)
    print(f"\nDataset saved successfully to: {TRAINING_DATA_PATH}")

if __name__ == "__main__":
    build_dataset()
