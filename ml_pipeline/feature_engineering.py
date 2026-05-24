"""
Feature engineering module for the Tree Prescriber pipeline.
Calculates ecological indices, soil texture classes, elevation bands,
and performs spatial clustering using a fitted KMeans model.
"""

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import KMeans
from config import NUMERIC_FEATURES, CATEGORICAL_FEATURES

def get_usda_texture_class(sand: float, clay: float, silt: float) -> str:
    """
    Classifies soil texture into USDA texture triangle classes based on sand, clay, silt percentages.
    """
    # Safeguard sum to 100%
    tot = sand + clay + silt
    if tot == 0:
        return "Loam"
    s_pct = (sand / tot) * 100
    c_pct = (clay / tot) * 100
    si_pct = (silt / tot) * 100

    if c_pct >= 40:
        if s_pct >= 45:
            return "Sandy Clay"
        elif si_pct >= 40:
            return "Silty Clay"
        else:
            return "Clay"
    elif c_pct >= 27 and c_pct < 40:
        if s_pct > 45:
            return "Sandy Clay Loam"
        elif si_pct <= 20:
            return "Clay Loam"
        else:
            return "Silty Clay Loam"
    else:  # clay < 27%
        if si_pct >= 50:
            if c_pct >= 12 and si_pct < 80:
                return "Silt Loam"
            elif si_pct >= 80:
                return "Silt"
            else:
                return "Silt Loam"
        else:  # silt < 50%
            if s_pct > 52:
                if c_pct >= 7 and s_pct > 52:
                    return "Sandy Loam"
                elif s_pct > 85:
                    return "Sand"
                else:
                    return "Loamy Sand"
            else:
                return "Loam"

def get_elevation_band(elevation: float) -> str:
    """
    Categorizes elevation into physical geographic zones of Nepal.
    """
    if elevation < 500:
        return "Terai Plains"
    elif elevation < 1000:
        return "Siwalik Hills"
    elif elevation < 2000:
        return "Middle Hills"
    elif elevation < 3000:
        return "High Mountains"
    else:
        return "High Himalaya"

class TreePrescriberFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Custom Scikit-Learn transformer for the Tree Prescriber feature pipeline.
    """
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = None
        self.fitted = False

    def fit(self, X: pd.DataFrame, y=None):
        """
        Fits spatial clustering model on coordinates.
        """
        # Copy to avoid side-effects
        X_df = X.copy()
        
        # Fit KMeans on latitude and longitude
        coords = X_df[["latitude", "longitude"]].values
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init=10)
        self.kmeans.fit(coords)
        self.fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms input DataFrame by adding engineered ecological features.
        """
        if not self.fitted:
            raise RuntimeError("Transformer must be fitted before calling transform.")

        X_df = X.copy()
        
        # 1. Nutrient Ratios (adding small epsilon to prevent division by zero)
        epsilon = 1e-6
        X_df["nk_ratio"] = X_df["total_nitrogen"] / (X_df["potassium"] + epsilon)
        X_df["np_ratio"] = X_df["total_nitrogen"] / (X_df["P2O5"] + epsilon)
        X_df["om_clay_ratio"] = X_df["organic_matter"] / (X_df["clay"] + epsilon)

        # 2. Climate Proxies
        # Nepal's temperature decreases by approx 6.5°C per 1000m elevation rise (lapse rate)
        # Latitudinal gradient also decreases temperature slightly going north
        X_df["temp_proxy"] = 30.0 - 0.0065 * X_df["elevation"] - (X_df["latitude"] - 26.3) * 1.5
        
        # Precipitation increases in the foothill basins but decreases in trans-Himalayan rain shadow areas
        # We model precipitation as peaking near central longitude/latitude valleys
        X_df["ppt_proxy"] = 2500.0 - abs(X_df["longitude"] - 84.5) * 220.0 - abs(X_df["latitude"] - 28.2) * 350.0
        X_df["ppt_proxy"] = X_df["ppt_proxy"].clip(lower=400.0, upper=4000.0)

        # 3. Categorical Elevation Band
        X_df["elevation_band"] = X_df["elevation"].apply(get_elevation_band)

        # 4. USDA Soil Texture Class
        X_df["soil_texture_class"] = X_df.apply(
            lambda r: get_usda_texture_class(r["sand"], r["clay"], r["silt"]), axis=1
        )

        # 5. Spatial Clusters
        coords = X_df[["latitude", "longitude"]].values
        cluster_labels = self.kmeans.predict(coords)
        X_df["spatial_cluster"] = [f"Cluster_{c}" for c in cluster_labels]

        return X_df
