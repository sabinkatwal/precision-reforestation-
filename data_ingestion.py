import pandas as pd
import numpy as np
from bbox import SHIVAPURI_BBOX

def generate_mock_data(n_samples=1000):
    """
    Simulates GBIF presence data and pseudo-absences based on environmental rules.
    Features: Latitude, Longitude, Elevation, NDVI, Slope, Aspect
    """
    np.random.seed(42)
    
    # Random points within Shivapuri BBOX
    lats = np.random.uniform(SHIVAPURI_BBOX['south'], SHIVAPURI_BBOX['north'], n_samples)
    lons = np.random.uniform(SHIVAPURI_BBOX['west'], SHIVAPURI_BBOX['east'], n_samples)
    
    # Synthetic Features
    # Elevation: typically 1000m to 3000m in this region
    elevations = np.random.uniform(500, 3500, n_samples)
    
    # NDVI: 0.1 (barren) to 0.9 (dense forest)
    ndvis = np.random.uniform(0.1, 0.9, n_samples)
    
    # Slope: 0 to 45 degrees
    slopes = np.random.uniform(0, 45, n_samples)
    
    # Aspect: 0 to 360 degrees
    aspects = np.random.uniform(0, 360, n_samples)
    
    data = []
    
    for i in range(n_samples):
        elev = elevations[i]
        ndvi = ndvis[i]
        slope = slopes[i]
        aspect = aspects[i]
        
        # Logic for Prescription (Species Labels)
        # 0: Unsuitable, 1: Salla, 2: Sisau, 3: Lali Gurans
        species = 0 
        
        # Sisau: Low altitude (< 1200m), High NDVI (Moisture)
        if elev < 1200 and ndvi > 0.5:
            species = 2
        # Salla: Mid-High altitude (1500-2500m), Lower NDVI (Drought tolerant), steep slopes
        elif 1500 <= elev <= 2500 and ndvi < 0.6 and slope > 15:
            species = 1
        # Lali Gurans: High altitude (> 2200m), High NDVI (Moist/Shaded)
        elif elev > 2200 and ndvi > 0.6:
            species = 3
            
        data.append({
            'latitude': lats[i],
            'longitude': lons[i],
            'elevation': elev,
            'ndvi': ndvi,
            'slope': slope,
            'aspect': aspect,
            'species': species
        })
        
    df = pd.DataFrame(data)
    df.to_csv('synthetic_tree_data.csv', index=False)
    print(f"Generated {n_samples} samples and saved to synthetic_tree_data.csv")

if __name__ == "__main__":
    generate_mock_data()
