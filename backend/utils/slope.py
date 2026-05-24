from __future__ import annotations

from math import atan, degrees, cos, radians
from typing import Optional


def meters_per_degree_lat(lat: float) -> float:
    return 111132.92 - 559.82 * cos(2 * radians(lat)) + 1.175 * cos(4 * radians(lat))


def meters_per_degree_lng(lat: float) -> float:
    return 111412.84 * cos(radians(lat)) - 93.5 * cos(3 * radians(lat))


def estimate_slope(center_elevation: float, north: Optional[float], south: Optional[float], east: Optional[float], west: Optional[float], lat: float, step_degrees: float = 0.01) -> float:
    lat_distance = meters_per_degree_lat(lat) * step_degrees
    lng_distance = meters_per_degree_lng(lat) * step_degrees
    rise_drops = []
    if north is not None:
        rise_drops.append(abs(north - center_elevation) / lat_distance)
    if south is not None:
        rise_drops.append(abs(south - center_elevation) / lat_distance)
    if east is not None:
        rise_drops.append(abs(east - center_elevation) / lng_distance)
    if west is not None:
        rise_drops.append(abs(west - center_elevation) / lng_distance)
    if not rise_drops:
        raise ValueError("No neighboring elevation samples available")
    steepest = max(rise_drops)
    return round(degrees(atan(steepest)), 2)


def terrain_class_from_slope(slope: float) -> str:
    if slope < 5:
        return "Flat"
    if slope < 15:
        return "Undulating"
    if slope < 30:
        return "Steep"
    return "Extremely Steep"
