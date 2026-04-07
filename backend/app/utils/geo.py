"""Geo utilities — helper functions for PostGIS operations."""
from sqlalchemy import func
from sqlalchemy.sql.expression import ClauseElement

def make_point(lng: float, lat: float) -> ClauseElement:
    """Create a PostGIS GEOGRAPHY POINT from lng/lat.
    
    NOTE: PostGIS uses (longitude, latitude) order — opposite of Google Maps.
    """
    return func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)

def within_radius(column, lng: float, lat: float, radius_meters: float) -> ClauseElement:
    """SQL expression: column IS within radius_meters of (lng, lat)."""
    return func.ST_DWithin(column, make_point(lng, lat), radius_meters)

# Default search radii (meters)
DRIVER_SEARCH_RADIUS_DEFAULT = 10_000   # 10km
DRIVER_SEARCH_RADIUS_MAX = 50_000       # 50km
