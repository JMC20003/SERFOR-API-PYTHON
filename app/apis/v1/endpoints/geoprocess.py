from fastapi import APIRouter, Body, HTTPException
from app.services.geo_service import get_area_and_percentage, get_vertice_and_total_area
from app.models.models import Feature, FeatureCollection
from shapely.geometry import shape
from shapely.ops import transform
"""
from pyproj import Transformer, CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
"""
import math

router = APIRouter()

@router.post("/calculate-area/", summary="Calcula el área de un feature GeoJSON")
def calculate_area(feature: Feature = Body(...)):
    """
    Recibe un feature GeoJSON, lo convierte a UTM, calcula su área y devuelve el área en hectáreas y su porcentaje.
    """
    area_hectares, percentage, properties = get_area_and_percentage(feature)
    return {"area_hectares": area_hectares, "percentage": percentage, "properties": properties}

@router.post("/analyze-geojson/", summary="Analiza todos los features de una FeatureCollection GeoJSON")
def analyze_geojson(feature_collection: FeatureCollection = Body(...)):
    """
    Recibe una FeatureCollection GeoJSON, procesa cada feature dentro de ella,
    convierte su geometría a la zona UTM apropiada, extrae los vértices en UTM,
    calcula el área total en hectáreas y devuelve estos datos junto con las propiedades del feature.
    """
    if not feature_collection.features:
        raise HTTPException(status_code=400, detail="FeatureCollection must contain at least one feature")

    results = []
    for feature in feature_collection.features:
        vertices_utm, area_hectares = get_vertice_and_total_area(feature.geometry)
        results.append({"vertices_utm": vertices_utm, "area_hectares": area_hectares, "properties": feature.properties})

    return results
