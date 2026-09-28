from fastapi import APIRouter, HTTPException, Body, Path, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services import geo_service
from app.db.session import engine, engine_titulohabilitante_area

router = APIRouter()

# Pydantic Models for Swagger Documentation

class TituloHabilitanteBody(BaseModel):
    codigo_th: str = Field(..., example="ZONF_MAN_BOS_LOC_1_A", description="Código del Título Habilitante a buscar.")

class FeatureProperties(BaseModel):
    NU_ID_TITULOHABILITANTE_AREA: int
    NU_ID_TITULOHABILITANTE: int
    NU_SUPERFICIE: float
    NU_SUPERFICIE_APROBADA: float
    TX_NOMBRE_CAPA: str
    TX_UBIGEO: str

class Feature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    codigo: Any
    features: List[Feature]

# Endpoints

def _area_titulo_habilitante(code: str):
    titulo = geo_service.buscar_titulo_habilitante(engine_titulohabilitante_area, code)
    if not titulo:
        raise HTTPException(status_code=404, detail="Título habilitante no encontrado")

    nu_id = titulo["NU_ID_TITULOHABILITANTE"]
    department = titulo["TX_DEPARTAMENTO_TH"]
    province = titulo["TX_PROVINCIA_TH"]
    district = titulo["TX_DISTRITO_TH"]

    return geo_service.obtener_titulo_habilitante_area(engine_titulohabilitante_area, nu_id, department, province, district)

@router.get(
    "/titulo-habilitante-area",
    summary="Obtener áreas de un Título Habilitante",
    description="Busca un Título Habilitante por su código y devuelve las áreas geoespaciales asociadas a él en formato GeoJSON. El código se envía como query param (slash-safe): ?tituloHabilitante=17-MAD-TAM%2FCON-PFDM-2019-018",
    response_model=FeatureCollection
)
def obtener_area_titulo_habilitante(tituloHabilitante: str = Query(..., description="Código o nombre parcial del Título Habilitante.")):
    """
    Obtiene las áreas de un Título Habilitante a partir de su código.

    - **tituloHabilitante**: Código del título habilitante (query param, soporta `/`).
    """
    try:
        return _area_titulo_habilitante(tituloHabilitante)
    except HTTPException:
        raise
    except Exception as e:
        print("❌ Error al ejecutar TituloHabilitante_area:", e)
        raise HTTPException(status_code=500, detail="Error al buscar Título Habilitante")

@router.get(
    "/titulo-habilitante-area/{th_area}",
    summary="Obtener áreas de un Título Habilitante",
    description="Busca un Título Habilitante por su código y devuelve las áreas geoespaciales asociadas a él en formato GeoJSON. Ruta legacy: no soporta códigos con `/`; usar `?tituloHabilitante=` en esos casos.",
    response_model=FeatureCollection
)
def get_titulo_habilitante_area(th_area: str = Path(..., description="Código o nombre parcial del Título Habilitante.")):
    """
    Obtiene las áreas de un Título Habilitante a partir de su código.
    Ruta legacy: no soporta códigos con `/`. Usar `?tituloHabilitante=` para códigos con `/`.

    - **th_area**: Código del título habilitante.
    """
    try:
        return _area_titulo_habilitante(th_area)
    except HTTPException:
        raise
    except Exception as e:
        print("❌ Error al ejecutar TituloHabilitante_area:", e)
        raise HTTPException(status_code=500, detail="Error al buscar Título Habilitante")

@router.post(
    "/titulo-habilitante",
    summary="Obtener geometría de un Título Habilitante",
    description="Recibe el código de un Título Habilitante y devuelve su representación geoespacial en formato GeoJSON.",
    response_model=FeatureCollection
)
def get_titulo_habilitante(body: TituloHabilitanteBody):
    """
    Obtiene la geometría de un Título Habilitante a partir de su código.

    - **codigo_th**: Código exacto del título habilitante.
    """
    try:
        return geo_service.obtener_titulo_habilitante(engine, body.codigo_th)
    except Exception as e:
        print("❌ Error al ejecutar TituloHabilitante:", e)
        raise HTTPException(status_code=500, detail="Error al buscar Título Habilitante")
