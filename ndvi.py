import os
import zipfile
import numpy as np
import rasterio
from pathlib import Path

def find_band(safe_dir, band_name):
    """Search for a specific Sentinel-2 band in the 10m resolution folder."""
    for root, dirs, files in os.walk(safe_dir):
        for file in files:
            if band_name in file and file.endswith('.jp2') and 'R10m' in root:
                return os.path.join(root, file)
    return None

def calculate_ndvi(safe_dir, output_path):
    """Calculates NDVI from Red (B04) and NIR (B08) bands and saves as GeoTIFF."""
    b04_path = find_band(safe_dir, '_B04_')
    b08_path = find_band(safe_dir, '_B08_')

    if not b04_path or not b08_path:
        print(f"Could not find required 10m bands (B04, B08) in {safe_dir}")
        return

    print(f"Red band: {b04_path}")
    print(f"NIR band: {b08_path}")

    # Open Red Band
    with rasterio.open(b04_path) as red_file:
        red = red_file.read(1).astype(float)
        profile = red_file.profile

    # Open NIR Band
    with rasterio.open(b08_path) as nir_file:
        nir = nir_file.read(1).astype(float)

    # Calculate NDVI (adding epsilon to prevent division by zero)
    ndvi = (nir - red) / (nir + red + 1e-10)

    print(f"NDVI range: {ndvi.min():.3f} to {ndvi.max():.3f}")
    print(f"Mean NDVI: {ndvi.mean():.3f}")

    # Update metadata profile for the output GeoTIFF
    profile.update(dtype=rasterio.float32, count=1, driver='GTiff')
    
    # Save the output file (will overwrite if exists)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(ndvi.astype(rasterio.float32), 1)
    print(f"Saved: {output_path}")


# Main execution block
if __name__ == "__main__":
    data_dir = Path("data")
    
    # Process all zip files in data/
    for zip_file in data_dir.glob("*.zip"):
        print(f"\n--- Processing: {zip_file.name} ---")
        
        if zip_file.stem.endswith('.SAFE'):
            extract_path = data_dir / zip_file.stem
            base_name = zip_file.stem[:-5] 
        else:
            extract_path = data_dir / (zip_file.stem + ".SAFE")
            base_name = zip_file.stem

        output_tiff = data_dir / f"ndvi_{base_name}.tif"

        # Force extraction if the CORRECT .SAFE folder doesn't exist
        if not extract_path.exists():
            print("Extracting zip archive...")
            with zipfile.ZipFile(zip_file, 'r') as z:
                z.extractall(data_dir)
            print("Extraction completed!")
        else:
            print(f"Found existing extraction folder: {extract_path}")

        # Calculate NDVI (Force overwrite)
        calculate_ndvi(str(extract_path), str(output_tiff))

    print("\nAll done!")