"""
Feature provider interface and implementations for the Tree Prescriber pipeline.
Provides a clean abstraction to swap between mock and real API datasets.
"""

from abc import ABC, abstractmethod
import json
import math
import os
import hashlib
import sqlite3
from pathlib import Path

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import NARC_API_KEY, NARC_API_URL, NUMERIC_FEATURES, CATEGORICAL_FEATURES

class FeatureProvider(ABC):
    """
    Abstract Base Class for retrieving environmental features at a given coordinate.
    Ensures that the ML pipeline interacts with the same schema regardless of the backend.
    """
    
    @abstractmethod
    def get_features(self, lat: float, lon: float) -> dict:
        """
        Retrieves a dictionary of environmental features for a given coordinate.
        
        Args:
            lat (float): Latitude of the target location.
            lon (float): Longitude of the target location.
            
        Returns:
            dict: Environmental feature vector conforming to the NARC schema.
        """
        pass


class MockFeatureProvider(FeatureProvider):
    """
    Mock implementation of FeatureProvider.
    Generates realistic, deterministic soil and environmental parameters for Nepal
    based on geographical gradients, physical rules, and spatial coordinate hashes.
    """

    def get_features(self, lat: float, lon: float) -> dict:
        # Validate coordinates are within reasonable bounds of Nepal
        if not (26.0 <= lat <= 31.0) or not (80.0 <= lon <= 89.0):
            raise ValueError(f"Coordinates ({lat}, {lon}) are outside the geographical bounds of Nepal.")

        # Normalize coordinates for gradient calculations
        # Nepal lat span: ~26.3 to 30.5; lon span: ~80.0 to 88.2
        lat_norm = (lat - 26.3) / (30.5 - 26.3)
        lat_norm = max(0.0, min(1.0, lat_norm))
        lon_norm = (lon - 80.0) / (88.2 - 80.0)
        lon_norm = max(0.0, min(1.0, lon_norm))

        # 1. Elevation (meters)
        # Nepal rises dramatically from South (Terai, ~60-200m) to North (Himalaya, >8000m)
        # We model this altitude profile using the normalized latitude
        base_elev = 80.0 + (lat_norm ** 2.2) * 5500.0
        # Add local terrain complexity (hills and valleys) using longitude waves
        terrain_ripple = 350.0 * math.sin(lon_norm * 14 * math.pi) * math.cos(lat_norm * 8 * math.pi)
        elevation = float(round(max(60.0, min(8848.0, base_elev + terrain_ripple)), 1))

        # 2. Soil pH
        # Forest and hill soils in Nepal are often acidic (4.5 - 6.0), while lowlands
        # and river basins can range towards neutral/alkaline (6.5 - 7.8).
        # We make pH lower (acidic) in mid-to-high elevations and higher in lowlands.
        elev_ph_modifier = -1.5 * (elevation / 3000.0) if elevation < 3000 else -1.5
        pH = float(round(7.2 + elev_ph_modifier + 0.4 * math.sin(lon * 5), 2))
        pH = max(4.0, min(8.5, pH))

        # Deterministic noise helper for minor chemical variations
        def _coord_noise(salt: str, scale: float) -> float:
            h = hashlib.md5(f"{lat:.5f}:{lon:.5f}:{salt}".encode('utf-8')).hexdigest()
            return (int(h[:8], 16) / 0xFFFFFFFF - 0.5) * scale

        # 3. Total Nitrogen (%) - typically 0.02% to 0.4% in Nepal
        # Richer in mid-elevation mixed forests, lower in sandy riverbanks and high rocky alpines
        nitrogen_base = 0.05 + 0.18 * math.exp(-((elevation - 1800) / 1000) ** 2)
        total_nitrogen = float(round(max(0.01, min(0.45, nitrogen_base + _coord_noise("nitrogen", 0.04))), 3))

        # 4. Organic Matter (%) - typically 0.5% to 8%
        # Strongly correlated with nitrogen in natural forest ecosystems
        organic_matter = float(round(max(0.2, min(10.0, total_nitrogen * 18.0 + 0.5 + _coord_noise("om", 0.8))), 2))

        # 5. Potassium (mg/kg) - typically 40 to 450
        potassium_base = 120.0 + 150.0 * (1.0 - lat_norm) + 50.0 * math.sin(lon * 4)
        potassium = float(round(max(20.0, min(500.0, potassium_base + _coord_noise("potassium", 30.0))), 1))

        # 6. P2O5 (Phosphorus, mg/kg) - typically 5 to 120
        p2o5_base = 15.0 + 60.0 * (1.0 - lat_norm * 0.7) * abs(math.cos(lon * 3))
        P2O5 = float(round(max(2.0, min(150.0, p2o5_base + _coord_noise("p2o5", 10.0))), 1))

        # 7. Boron (mg/kg) - micronutrient, typically 0.05 to 3.0
        boron = float(round(max(0.01, min(4.0, 0.4 + 0.5 * lat_norm + _coord_noise("boron", 0.15))), 2))

        # 8. Zinc (mg/kg) - micronutrient, typically 0.1 to 6.0
        zinc = float(round(max(0.05, min(8.0, 1.2 + 0.8 * (1.0 - lat_norm) + _coord_noise("zinc", 0.3))), 2))

        # 9. Soil Texture (Sand, Silt, Clay percentages adding to 100)
        # Clay is higher in lowlands and plains, Sand is higher in steep mountain regions
        base_clay = 15.0 + (1.0 - lat_norm) * 20.0 + _coord_noise("clay", 6.0)
        base_sand = 20.0 + lat_norm * 45.0 + _coord_noise("sand", 8.0)
        base_clay = max(5.0, min(80.0, base_clay))
        base_sand = max(5.0, min(80.0, base_sand))
        
        sum_cs = base_clay + base_sand
        if sum_cs > 90.0:
            scale = 90.0 / sum_cs
            base_clay *= scale
            base_sand *= scale

        clay = float(round(base_clay, 1))
        sand = float(round(base_sand, 1))
        silt = float(round(100.0 - clay - sand, 1))

        # 10. Parent Soil/Material
        parent_materials = ["Alluvium", "Colluvium", "Residuum", "Gneissic Saprolite", "Quartzite", "Shale"]
        h_parent = int(hashlib.md5(f"{lat:.4f}:{lon:.4f}:parent".encode('utf-8')).hexdigest()[:4], 16)
        parent_soil = parent_materials[h_parent % len(parent_materials)]

        # 11. Administrative Regions (Province, District, Gaupalika/Municipality)
        # Simple bounding box classifier for Nepal's 7 provinces
        if lon < 81.3:
            province = "Sudurpashchim Province"
            districts = ["Darchula", "Baitadi", "Dadeldhura", "Kanchanpur", "Kailali", "Doti", "Achham", "Bajhang", "Bajura"]
        elif lon < 83.0:
            province = "Karnali Province"
            districts = ["Humla", "Mugu", "Dolpa", "Jumla", "Kalikot", "Dailekh", "Jajarkot", "Surkhet", "Salyan", "Rukum West"]
        elif lon < 84.4 and lat < 28.3:
            province = "Lumbini Province"
            districts = ["Rupandehi", "Kapilvastu", "Arghakhanchi", "Gulmi", "Palpa", "Nawalparasi West", "Dang", "Pyuthan", "Rolpa", "Rukum East", "Banke", "Bardiya"]
        elif lon < 84.8 and lat >= 28.3:
            province = "Gandaki Province"
            districts = ["Mustang", "Manang", "Kaski", "Myagdi", "Baglung", "Parbat", "Syangja", "Tanahun", "Lamjung", "Gorkha", "Nawalpur"]
        elif lon < 86.2 and lat >= 27.4:
            province = "Bagmati Province"
            districts = ["Kathmandu", "Lalitpur", "Bhaktapur", "Chitwan", "Makwanpur", "Dhading", "Nuwakot", "Rasuwa", "Sindhupalchok", "Kavrepalanchok", "Dolakha", "Ramechhap", "Sindhuli"]
        elif lon < 86.4 and lat < 27.4:
            province = "Madhesh Province"
            districts = ["Saptari", "Siraha", "Dhanusha", "Mahottari", "Sarlahi", "Rautahat", "Bara", "Parsa"]
        else:
            province = "Koshi Province"
            districts = ["Solukhumbu", "Sankhuwasabha", "Taplejung", "Okhaldhunga", "Khotang", "Bhojpur", "Dhankuta", "Terhathum", "Panchthar", "Ilam", "Jhapa", "Morang", "Sunsari", "Udayapur"]

        # Select district deterministically from coordinate hash
        h_dist = int(hashlib.md5(f"{lat:.4f}:{lon:.4f}:district".encode('utf-8')).hexdigest()[:4], 16)
        district = districts[h_dist % len(districts)]

        # Generate a placeholder Gaupalika (Rural Municipality)
        gaupalika = f"{district}-RM-{1 + (h_dist % 4)}"

        return {
            "elevation": elevation,
            "pH": pH,
            "organic_matter": organic_matter,
            "total_nitrogen": total_nitrogen,
            "potassium": potassium,
            "P2O5": P2O5,
            "boron": boron,
            "zinc": zinc,
            "sand": sand,
            "clay": clay,
            "silt": silt,
            "parent_soil": parent_soil,
            "province": province,
            "district": district,
            "gaupalika": gaupalika
        }


class NARCFeatureProvider(FeatureProvider):
    """
    NARC FeatureProvider implementation.
    Queries the NARC soil API for coordinates and caches responses locally.
    """

    def __init__(self, api_url: str = None, api_key: str = None, cache_db: str = None):
        self.api_url = api_url or NARC_API_URL
        self.api_key = api_key or NARC_API_KEY
        self.cache_db_path = Path(cache_db or Path(__file__).resolve().parent / "narc_cache.db")

        if not self.api_url:
            raise ValueError(
                "NARC API URL is not configured. Set NARC_API_URL or disable USE_NARC_PROVIDER."
            )

        self._init_cache()

    def _init_cache(self) -> None:
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS narc_cache (cache_key TEXT PRIMARY KEY, payload TEXT, updated_at REAL)"
            )
            conn.commit()

    def _check_cache(self, key: str) -> dict | None:
        with sqlite3.connect(self.cache_db_path) as conn:
            row = conn.execute(
                "SELECT payload FROM narc_cache WHERE cache_key = ?", (key,)
            ).fetchone()
            if row:
                return json.loads(row[0])
        return None

    def _write_cache(self, key: str, data: dict) -> None:
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO narc_cache (cache_key, payload, updated_at) VALUES (?, ?, strftime('%s','now'))",
                (key, json.dumps(data)),
            )
            conn.commit()

    @retry(
        retry=retry_if_exception_type((requests.RequestException, ValueError)),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _fetch_raw_features(self, lat: float, lon: float) -> dict:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.get(
            self.api_url,
            params={"latitude": lat, "longitude": lon},
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Unexpected NARC API response format")
        return data

    def get_features(self, lat: float, lon: float) -> dict:
        cache_key = f"{lat:.5f}:{lon:.5f}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached

        raw_data = self._fetch_raw_features(lat, lon)
        normalized = self._normalize_response(raw_data)
        self._write_cache(cache_key, normalized)
        return normalized

    def _find_value(self, data: dict, candidates: list[str]):
        if not isinstance(data, dict):
            return None

        for candidate in candidates:
            if candidate in data:
                return data[candidate]

        for value in data.values():
            if isinstance(value, dict):
                found = self._find_value(value, candidates)
                if found is not None:
                    return found
        return None

    def _cast_numeric(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return float(value.replace(",", "."))
            except ValueError:
                return None
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _normalize_response(self, raw_data: dict) -> dict:
        mapping = {
            "elevation": ["elevation", "elev", "altitude", "height"],
            "pH": ["pH", "ph", "soil_ph", "soil_pH"],
            "organic_matter": ["organic_matter", "organicMatter", "organic matter", "om"],
            "total_nitrogen": ["total_nitrogen", "nitrogen", "n", "totalNitrogen"],
            "potassium": ["potassium", "k", "potassium_mgkg", "k_mgkg"],
            "P2O5": ["P2O5", "p2o5", "phosphorus", "phosphorus_oxide"],
            "boron": ["boron", "b"],
            "zinc": ["zinc", "zn"],
            "sand": ["sand", "sand_percent", "sand_pct"],
            "clay": ["clay", "clay_percent", "clay_pct"],
            "silt": ["silt", "silt_percent", "silt_pct"],
            "parent_soil": ["parent_soil", "parentSoil", "soil_parent_material", "parent_material"],
            "province": ["province", "state", "admin1"],
            "district": ["district", "admin2", "county"],
            "gaupalika": ["gaupalika", "municipality", "local_body", "rural_municipality"],
        }

        normalized: dict = {}
        for feature, candidates in mapping.items():
            value = self._find_value(raw_data, candidates)
            if feature in NUMERIC_FEATURES:
                casted = self._cast_numeric(value)
                if casted is None:
                    raise ValueError(f"Missing or invalid required numeric NARC feature: {feature}")
                normalized[feature] = casted
            else:
                normalized[feature] = str(value).strip() if value is not None else "Unknown"

        return normalized
