from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services import geo_service
from app.db.session import engine, engine_cobertura
from shapely import wkt as wkt_lib
from shapely.geometry import shape as geom_shape, mapping
from shapely.ops import unary_union
import geojson

router = APIRouter()

# Pydantic Models for Swagger Documentation

class InterseccionRequest(BaseModel):
    table: str = Field(..., example="public.bosques_secos", description="Nombre de la tabla con la que se realizará la intersección, en formato `schema.tabla`.")
    geojson: Dict[str, Any] = Field(..., example={"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[-79, -5], [-78, -5], [-78, -6], [-79, -6], [-79, -5]]]}, "properties": {}}, description="Objeto GeoJSON (Feature o FeatureCollection) que define el área de interés.")

class GeoJSONBody(BaseModel):
    geojson: Dict[str, Any] = Field(..., example={"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[-79, -5], [-78, -5], [-78, -6], [-79, -6], [-79, -5]]]}, "properties": {}}, description="Objeto GeoJSON (Feature o FeatureCollection) que define el área de interés.")

class InterseccionProperties(BaseModel):
    id: Optional[Any] = Field(None, description="ID de la feature intersectada.")
    hectareas: Optional[float] = Field(None, description="Área de la intersección en hectáreas.")
    km2: Optional[float] = Field(None, description="Área de la intersección en kilómetros cuadrados.")
    srid: Optional[int] = Field(None, description="SRID del resultado.")

class CoberturaProperties(InterseccionProperties):
    pass

class MultipleProperties(InterseccionProperties):
    tabla_origen: Optional[str] = Field(None, description="Tabla de origen de la feature intersectada.")

class DominioProperties(BaseModel):
    nombre_capa: Optional[str] = Field(None, description="Nombre de la capa con la que hubo intersección.")
    estado_interseccion: bool = Field(..., description="Indica si hay o no intersección.")
    medida: float = Field(..., description="Medida de la intersección (e.g., área).")

class Feature(BaseModel):
    type: str = "Feature"
    geometry: Optional[Dict[str, Any]]
    properties: Dict[str, Any]

class InterseccionFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[Feature]

# Endpoints

@router.post(
    "/interseccion",
    summary="Calcular intersección con una capa específica",
    description="Realiza una intersección geoespacial entre un GeoJSON de entrada y una tabla de la base de datos especificada.",
    response_model=InterseccionFeatureCollection
)
def interseccion(req: InterseccionRequest):
    if "." not in req.table:
        raise HTTPException(status_code=400, detail="Formato de tabla inválido. Debe ser 'schema.tabla'.")
    
    schema, table = req.table.split(".")
    try:
        geom = geojson.loads(geojson.dumps(req.geojson["geometry"]))
        wkt_geom = wkt_lib.dumps(geom_shape(geom))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GeoJSON inválido: {e}")

    try:
        return geo_service.procesar_interseccion(engine, schema, table, wkt_geom)
    except Exception as e:
        print("❌ Intersección error:", e)
        raise HTTPException(status_code=500, detail="Error al procesar intersección")

@router.post(
    "/interseccion/cobertura",
    summary="Calcular intersección con la capa de cobertura vegetal",
    description="Calcula la intersección entre un GeoJSON de entrada y la capa de cobertura vegetal.",
    response_model=InterseccionFeatureCollection
)
def interseccion_cobertura(req: GeoJSONBody):
    try:
        geo = req.geojson
        if geo["type"] == "FeatureCollection":
            geometries = [geom_shape(f["geometry"]) for f in geo["features"]]
            unioned = unary_union(geometries)
        elif geo["type"] == "Feature":
            unioned = geom_shape(geo["geometry"])
        else:
            raise ValueError("Tipo GeoJSON no soportado")

        wkt_geom = wkt_lib.dumps(unioned)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GeoJSON inválido: {e}")

    try:
        return geo_service.procesar_interseccion_cobertura(engine_cobertura, wkt_geom)
    except Exception as e:
        print("❌ Error en intersección de cobertura vegetal:", e)
        raise HTTPException(status_code=500, detail="Error al procesar la intersección de cobertura vegetal")

@router.post(
    "/interseccion/multiple",
    summary="Calcular intersecciones con múltiples capas",
    description="Ejecuta una intersección del GeoJSON de entrada contra un conjunto predefinido de capas.",
    response_model=InterseccionFeatureCollection
)
def interseccion_multiple(req: GeoJSONBody):
    try:
        geo = req.geojson
        if geo["type"] == "FeatureCollection":
            geometries = [geom_shape(f["geometry"]) for f in geo["features"]]
            unioned = unary_union(geometries)
        elif geo["type"] == "Feature":
            unioned = geom_shape(geo["geometry"])
        else:
            raise ValueError("Tipo GeoJSON no soportado")

        wkt_geom = wkt_lib.dumps(unioned)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GeoJSON inválido: {e}")

    try:
        return geo_service.procesar_interseccion_multiple(engine_cobertura, wkt_geom)
    except Exception as e:
        print("❌ Error al ejecutar intersección múltiple:", e)
        raise HTTPException(status_code=500, detail="Error al procesar la intersección múltiple")

@router.post(
    "/interseccion/dominio",
    summary="Calcular intersección con la capa de dominio",
    description="Calcula la intersección entre un GeoJSON de entrada y la capa de dominio para análisis específicos.",
    response_model=InterseccionFeatureCollection
)
def interseccion_dominio(req: GeoJSONBody):
    try:
        geo = req.geojson
        if geo["type"] == "FeatureCollection":
            geometries = [geom_shape(f["geometry"]) for f in geo["features"]]
            unioned = unary_union(geometries)
        elif geo["type"] == "Feature":
            unioned = geom_shape(geo["geometry"])
        else:
            raise ValueError("Tipo GeoJSON no soportado")

        wkt_geom = wkt_lib.dumps(unioned)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GeoJSON inválido: {e}")

    try:
        return geo_service.procesar_interseccion_dominio(engine_cobertura, wkt_geom)
    except Exception as e:
        print("❌ Error al ejecutar interseccion dominio:", e)
        raise HTTPException(status_code=500, detail="Error al procesar la interseccion dominio")
