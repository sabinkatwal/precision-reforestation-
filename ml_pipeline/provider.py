"""
Feature provider interface and implementations for the Tree Prescriber pipeline.
Provides a clean abstraction to swap between mock and real API datasets.
"""

from abc import ABC, abstractmethod
import math
import hashlib

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
    NARC API Implementation (LATER).
    This acts as a placeholder for integrating the real REST API once it goes live.
    Implements caching (to disk/sqlite or Redis) and retry decorators.
    """

    def __init__(self, api_url: str = None, cache_db: str = "narc_cache.db"):
        self.api_url = api_url or "https://api.narc-nepal.gov/v1/soil-query"
        self.cache_db = cache_db
        # TODO: Initialize caching database (SQLite or Redis client) here

    def get_features(self, lat: float, lon: float) -> dict:
        """
        Queries the NARC REST API to fetch real soil and environmental parameters.
        Includes a local cache check before calling the remote server.
        """
        # TODO: Step 1. Check local cache (e.g. SQLite database) for coordinates (rounded to 4 decimal places)
        # cache_key = f"{lat:.4f}:{lon:.4f}"
        # cached_result = self._check_cache(cache_key)
        # if cached_result:
        #     return cached_result

        # TODO: Step 2. Execute HTTP GET/POST request with retry logic (e.g. using tenacity or a manual retry loop)
        # headers = {"Authorization": "Bearer YOUR_NARC_API_KEY"}
        # params = {"latitude": lat, "longitude": lon}
        # response = requests.get(self.api_url, params=params, headers=headers, timeout=10)
        # response.raise_for_status()
        # raw_data = response.json()

        # TODO: Step 3. Normalize API field names and handle missing values
        # e.g., mapping "organicmatter" -> "organic_matter", filling missing micronutrients with median values
        # normalized = self._normalize_response(raw_data)

        # TODO: Step 4. Write to local cache
        # self._write_cache(cache_key, normalized)

        # Raise an exception for now since this provider is not yet live
        raise NotImplementedError(
            "NARCFeatureProvider is not active yet. "
            "Please configure the application to use MockFeatureProvider during development."
        )

    def _check_cache(self, key: str) -> dict:
        # TODO: Implement database cache lookup
        return {}

    def _write_cache(self, key: str, data: dict):
        # TODO: Implement caching write operation
        pass

    def _normalize_response(self, raw_data: dict) -> dict:
        # TODO: Implement response mapping and standard validation checks
        return raw_data
