from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import requests
import geojson

router = APIRouter()

# =============================================================================
# Modelos Pydantic para la documentación de Swagger
# =============================================================================

class FiltrosUnidadesAprovechamiento(BaseModel):
    """
    Filtros para consultar las Unidades de Aprovechamiento.
    Al menos uno de los filtros debe tener valor.
    """
    arffs: Optional[str] = Field(
        default="",
        description="Código de la Autoridad Forestal (ARFFS). Ejemplo: '3' para SERFOR"
    )
    estado: Optional[int] = Field(
        default=None,
        description="Estado de la unidad: 1=No Otorgada, 2=Concesionada, 3=No Concesionada, etc."
    )
    lote: Optional[str] = Field(
        default="",
        description="Número de la Unidad/Lote. Ejemplo: '001'"
    )
    objectid: Optional[str] = Field(
        default="",
        description="ID del objeto espacial (OBJECTID del layer de ArcGIS)"
    )


class UnidadesAprovechamientoRequest(BaseModel):
    """
    Request para consultar Unidades de Aprovechamiento.
    """
    filtros: FiltrosUnidadesAprovechamiento = Field(
        ...,
        description="Diccionario de filtros para la consulta"
    )


class GeoJSONGeometry(BaseModel):
    """Geometría GeoJSON."""
    type: str
    coordinates: List[Any]


class FeatureProperties(BaseModel):
    """Propiedades de una feature de Unidad de Aprovechamiento."""
    OBJECTID: Optional[int] = Field(None, description="ID único del objeto espacial")
    FUENTE: Optional[str] = Field(None, description="Entidad generadora", max_length=100)
    DOCREG: Optional[str] = Field(None, description="Documento que avala el registro", max_length=100)
    FECREG: Optional[str] = Field(None, description="Fecha de registro del objeto")
    OBSERV: Optional[str] = Field(None, description="Observación o referencia", max_length=255)
    ZONUTM: Optional[int] = Field(None, description="Zona UTM (17, 18, 19)")
    ORIGEN: Optional[int] = Field(None, description="Origen del objeto (1=COORD, 2=SHP, 3=BD)")
    LOTE: Optional[str] = Field(None, description="Número de la Unidad", max_length=10)
    NOMDEP: Optional[str] = Field(None, description="Nombre de departamento", max_length=255)
    CONTRA: Optional[str] = Field(None, description="Código de contrato de la concesión", max_length=300)
    NOMTIT: Optional[str] = Field(None, description="Nombre del titular de la concesión", max_length=255)
    NOMREL: Optional[str] = Field(None, description="Nombre del representante legal", max_length=255)
    CONCUR: Optional[int] = Field(None, description="Número de concurso que fue otorgada la concesión")
    MODOTO: Optional[int] = Field(None, description="Modalidad de Otorgamiento (1=No asignado, 2=Concurso Público, 3=Procedimiento Abreviado)")
    FECOTO: Optional[str] = Field(None, description="Fecha de proceso de la modalidad de otorgamiento")
    SUPSIG: Optional[float] = Field(None, description="Superficie calculada (hectáreas)")
    SUPAPR: Optional[float] = Field(None, description="Superficie aprobada (hectáreas)")
    DOCLEG: Optional[str] = Field(None, description="Documento legal o resolución", max_length=100)
    FECLEG: Optional[str] = Field(None, description="Fecha de documento legal")
    ESTUA: Optional[int] = Field(None, description="Estado de la unidad (1=No Otorgada, 2=Concesionada, etc.)")
    FECEUA: Optional[str] = Field(None, description="Fecha de estado de la unidad")
    AUTFOR: Optional[int] = Field(None, description="Nombre de la ARFFS (autoridad forestal)")


class Feature(BaseModel):
    """Feature GeoJSON de Unidad de Aprovechamiento."""
    type: str = "Feature"
    geometry: Optional[GeoJSONGeometry]
    properties: FeatureProperties


class CapaResultado(BaseModel):
    """Resultado de una capa consultada."""
    nombreCapa: str = Field(..., description="Nombre de la capa")
    codigoCapa: str = Field(..., description="Código identificador de la capa")
    numeroGeometrias: int = Field(..., description="Cantidad de geometrías encontradas")
    geoJson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON con las features resultantes")


class DataResultado(BaseModel):
    """Datos de la respuesta exitosa."""
    mensaje: str = Field(..., description="Mensaje descriptivo del resultado")
    nroCapasConsultadas: int = Field(..., description="Número de capas consultadas")
    nroCapasConResultado: int = Field(..., description="Número de capas con resultados")
    capas: List[CapaResultado] = Field(..., description="Lista de capas con resultados")


class UnidadesAprovechamientoResponse(BaseModel):
    """
    Respuesta del servicio de Unidades de Aprovechamiento.
    """
    isSuccess: bool = Field(..., description="Indica si la consulta fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    data: Optional[DataResultado] = Field(None, description="Datos de la consulta exitosa")


# =============================================================================
# Constantes y Configuración
# =============================================================================

# URL del servicio ArcGIS REST de SERFOR
ARCGIS_SERVICE_URL = "https://geo.serfor.gob.pe/geoservicios/rest/services/Servicios_OGC/Modalidad_Acceso/MapServer/5/query"

# Mapeo de códigos ARFFS (Autoridad Forestal)
# Según ArcGIS: [1: SERFOR] , [2: GORE Loreto] , [3: GORE Ucayali] , ...20 more...
ARFFS_MAPPING = {
    "1": "SERFOR",
    "2": "GORE Loreto",
    "3": "GORE Ucayali",
    "4": "GORE Amazonas",
    "5": "GORE San Martín",
    "6": "GORE Madre de Dios",
    "7": "GORE Huánuco",
    "8": "GORE Pasco",
    "9": "GORE Junín",
    "10": "GORE Ayacucho",
    "11": "GORE Cusco",
    "12": "GORE Apurímac",
    "13": "GORE Arequipa",
    "14": "GORE Puno",
    "15": "GORE Moquegua",
    "16": "GORE Tacna",
    "17": "GORE La Libertad",
    "18": "GORE Cajamarca",
    "19": "GORE Lambayeque",
    "20": "GORE Piura",
    "21": "GORE Tumbes",
}

# Mapeo de estados (ESTUA)
ESTADOS_MAPPING = {
    1: "No Otorgada",
    2: "Concesionada",
    3: "No Concesionada",
    4: "Vigente",
    5: "Caducada",
    6: "Rescindida",
    7: "Anulada",
    8: "En Proceso"
}


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/aprovechamiento",
    summary="Consultar Unidades de Aprovechamiento Forestal",
    description="""
    **Servicio para consultar las Unidades de Aprovechamiento** por Autoridad Forestal (ARFFS),
    Estado, Lote o ID del objeto espacial.

    ## Filtros Disponibles:

    - **arffs**: Código de la Autoridad Forestal. Ejemplo: '1' para SERFOR, '2' para GORE Loreto, '3' para GORE Ucayali, etc.
    - **estado**: Estado de la unidad (1=No Otorgada, 2=Concesionada, 3=No Concesionada, etc.)
    - **lote**: Número de la Unidad/Lote
    - **objectid**: ID del objeto espacial (OBJECTID del layer)

    ## Importante:

    - Al menos **uno** de los filtros debe tener valor
    - Los filtros son acumulativos (se aplica lógica AND)
    - El servicio consulta directamente el layer 5 del servicio ArcGIS de SERFOR
    - Use el endpoint `/aprovechamiento/arffs` para obtener el listado completo de autoridades forestales
    
    ## Campos Retornados:
    
    La respuesta incluye información completa de cada unidad:
    - Código de contrato (CONTRA)
    - Nombre del titular (NOMTIT)
    - Representante legal (NOMREL)
    - Superficie (SUPSIG, SUPAPR) en hectáreas
    - Estado actual (ESTUA)
    - Modalidad de otorgamiento (MODOTO)
    - Documento legal (DOCLEG, FECLEG)
    - Geometría espacial en formato GeoJSON
    """,
    response_model=UnidadesAprovechamientoResponse,
    tags=["Unidades de Aprovechamiento"]
)
def consultar_unidades_aprovechamiento(request: UnidadesAprovechamientoRequest):
    """
    Consulta las Unidades de Aprovechamiento Forestal aplicando los filtros especificados.
    
    - **filtros.arffs**: Código de la Autoridad Forestal (ARFFS)
    - **filtros.estado**: Estado de la unidad (ver catálogo en descripción)
    - **filtros.lote**: Número de lote/unidad
    - **filtros.objectid**: ID del objeto espacial
    
    Retorna un GeoJSON con las unidades que coinciden con los filtros.
    """
    filtros = request.filtros
    
    # Validar que al menos un filtro tenga valor válido
    # estado=0 significa "sin filtro", por lo tanto no cuenta como filtro válido
    tiene_arffs = filtros.arffs is not None and filtros.arffs.strip()
    tiene_estado = filtros.estado is not None and filtros.estado >= 1
    tiene_lote = filtros.lote is not None and filtros.lote.strip()
    tiene_objectid = filtros.objectid is not None and filtros.objectid.strip()
    
    if not any([tiene_arffs, tiene_estado, tiene_lote, tiene_objectid]):
        raise HTTPException(
            status_code=400,
            detail="Solicitud incompleta, No incorporó los filtros"
        )
    
    try:
        # Construir where clause para ArcGIS
        where_clauses = []

        if tiene_arffs:
            where_clauses.append(f"AUTFOR = {filtros.arffs.strip()}")

        if tiene_estado:
            where_clauses.append(f"ESTUA = {filtros.estado}")

        if tiene_lote:
            lote_valor = filtros.lote.strip().replace("'", "''")
            where_clauses.append(f"LOTE = '{lote_valor}'")

        if tiene_objectid:
            where_clauses.append(f"OBJECTID = {filtros.objectid.strip()}")

        where_clause = " AND ".join(where_clauses)
        
        # Parámetros para la consulta a ArcGIS
        params = {
            "where": where_clause,
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true",
            "spatialRel": "esriSpatialRelIntersects",
            "outSR": '{"wkid":4326}'
        }
        
        # Realizar consulta al servicio ArcGIS
        response = requests.get(ARCGIS_SERVICE_URL, params=params, timeout=60)
        response.raise_for_status()
        
        arcgis_result = response.json()
        
        # Procesar resultado
        features_count = 0
        geojson_result = None
        
        if arcgis_result.get("type") == "FeatureCollection":
            features = arcgis_result.get("features", [])
            features_count = len(features)
            
            if features_count > 0:
                geojson_result = arcgis_result
        
        # Construir respuesta
        data_result = DataResultado(
            mensaje=f"Se encontraron resultados en 1 capa(s)" if features_count > 0 else "No se encontraron resultados",
            nroCapasConsultadas=1,
            nroCapasConResultado=1 if features_count > 0 else 0,
            capas=[
                CapaResultado(
                    nombreCapa="Unidad_de_Aprovechamiento",
                    codigoCapa="UA-001",
                    numeroGeometrias=features_count,
                    geoJson=geojson_result
                )
            ]
        )
        
        return UnidadesAprovechamientoResponse(
            isSuccess=True,
            message="Consulta exitosa",
            data=data_result
        )
        
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Timeout al consultar el servicio de ArcGIS. Intente nuevamente."
        )
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al consultar ArcGIS: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Error al conectar con el servicio de ArcGIS: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error en unidades_aprovechamiento: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        )


@router.get(
    "/aprovechamiento/estados",
    summary="Obtener catálogo de Estados de Unidades",
    description="Retorna el catálogo de estados posibles para las Unidades de Aprovechamiento.",
    tags=["Unidades de Aprovechamiento"]
)
def obtener_estados_catalogo():
    """
    Obtiene el catálogo de estados disponibles para las Unidades de Aprovechamiento.
    """
    return {
        "isSuccess": True,
        "message": "Catálogo obtenido exitosamente",
        "data": {
            "estados": [
                {"codigo": k, "descripcion": v}
                for k, v in ESTADOS_MAPPING.items()
            ]
        }
    }


@router.get(
    "/aprovechamiento/arffs",
    summary="Obtener catálogo de ARFFS",
    description="Retorna el catálogo de Autoridades Forestales (ARFFS) disponibles.",
    tags=["Unidades de Aprovechamiento"]
)
def obtener_arffs_catalogo():
    """
    Obtiene el catálogo de Autoridades Forestales disponibles.
    """
    return {
        "isSuccess": True,
        "message": "Catálogo obtenido exitosamente",
        "data": {
            "arffs": [
                {"codigo": k, "nombre": v}
                for k, v in sorted(ARFFS_MAPPING.items(), key=lambda x: int(x[0]))
            ]
        }
    }
