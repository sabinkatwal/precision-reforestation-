"""
Central configuration for the Nepal Tree Prescriber machine learning pipeline.
Defines geographic bounds, file paths, feature schemas, and model settings.
"""

import os
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "ml_pipeline" / "models"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Geographic Bounds for Nepal
NEPAL_BBOX = {
    "min_lat": 26.3,
    "max_lat": 30.5,
    "min_lon": 80.0,
    "max_lon": 88.2
}

# Occurrence Files
OCCURRENCE_FILES = [
    DATA_DIR / "Dalbergia sissoo" / "occurrence.txt",
    DATA_DIR / "Pinus roxburghii Sarg" / "occurrence.txt"
]

# Output Files
TRAINING_DATA_PATH = DATA_DIR / "training_dataset.csv"
MODEL_PATH = MODEL_DIR / "tree_model.joblib"
ENCODERS_PATH = MODEL_DIR / "encoders.joblib"

# NARC API integration settings
NARC_API_URL = os.getenv("NARC_API_URL", "").strip()
NARC_API_KEY = os.getenv("NARC_API_KEY", "").strip()
USE_NARC_PROVIDER = os.getenv("USE_NARC_PROVIDER", "false").strip().lower() in ("1", "true", "yes")

# Soil & Environmental Features Schema
NUMERIC_FEATURES = [
    "elevation",
    "pH",
    "organic_matter",
    "total_nitrogen",
    "potassium",
    "P2O5",
    "boron",
    "zinc",
    "sand",
    "clay",
    "silt"
]

CATEGORICAL_FEATURES = [
    "parent_soil",
    "province",
    "district",
    "gaupalika"
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Engineered Features to be created in the pipeline
ENGINEERED_NUMERIC = [
    "nk_ratio",         # total_nitrogen / potassium
    "np_ratio",         # total_nitrogen / P2O5
    "om_clay_ratio",    # organic_matter / clay
    "temp_proxy",       # temperature proxy based on latitude and elevation
    "ppt_proxy"         # precipitation proxy based on coordinates
]

ENGINEERED_CATEGORICAL = [
    "elevation_band",
    "soil_texture_class",
    "spatial_cluster"
]

MODEL_FEATURES = ALL_FEATURES + ENGINEERED_NUMERIC + ENGINEERED_CATEGORICAL
