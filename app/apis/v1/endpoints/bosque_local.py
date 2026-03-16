from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from app.services.geo_service import (
    registrar_bosque_local,
    listar_bosque_local_geometrias,
    eliminar_bosque_local_geometria
)
from app.services.geo_serfor_service import (
    obtener_zonificacion_geoserfor
)
from app.db.session import engine_titulohabilitante_area as engine

router = APIRouter()


# --- Pydantic Models ---

class BosqueLocalRequest(BaseModel):
    """
    Payload para registrar una nueva geometría de Bosque Local.
    Campos obligatorios: idSolicitud, idArchivo, tipoGeometria, nombreCapa, 
                         colorCapa, codigoSeccion, geometriaGeoJSON, idUsuarioRegistro
    """
    idSolicitud: int
    idArchivo: Optional[int] = None
    tipoGeometria: str  # Punto, Línea, Polígono
    zonaUtm: int = 18  # Default: zona UTM 18
    idDist: str = "000000"  # Default: UBIGEO genérico
    vertice: int = 0  # Default: 0
    sector: str = ""  # Default: vacío
    nombreCapa: str
    colorCapa: str
    codigoSeccion: str
    geometriaGeoJSON: Dict[str, Any]  # GeoJSON Feature o Geometry
    srid: int = 4326  # Default WGS84 (Geográfico)
    propiedad: Optional[Dict[str, Any]] = None
    idUsuarioRegistro: int


class BosqueLocalResponse(BaseModel):
    """
    Respuesta del registro de geometría de Bosque Local.
    """
    idBosqueLocalGeometria: int


class BosqueLocalGeometriaItem(BaseModel):
    """
    Item individual de geometría de Bosque Local.
    """
    NU_ID_BL_GEOMETRIA: int
    NU_ID_SOLICITUD: int
    NU_ID_ARCHIVO: Optional[int] = None
    TX_TIPO_GEOMETRIA: str
    NU_ZONA_UTM: int
    TX_IDDIST: str
    NU_VERTICE: int
    TX_SECTOR: str
    TX_CODIGO_SECCION: str
    TX_NOMBRE_CAPA: str
    TX_COLOR_CAPA: Optional[str] = None
    geometry_geojson: Optional[Dict[str, Any]] = None
    NU_SRID: Optional[int] = None
    TX_PROPIEDAD: Optional[Dict[str, Any]] = None
    NU_AREA_HA: float
    FE_FECHA_REGISTRO: str
    NU_ID_USUARIO_REGISTRO: int
    TX_NOMBRE_ARCHIVO_FISICO: Optional[str] = None


class BosqueLocalDeleteRequest(BaseModel):
    """
    Payload para eliminar una geometría de Bosque Local.
    """
    idBlGeometria: int
    idUsuario: int


class ObtenerZonificacionRequest(BaseModel):
    """
    Payload para obtener la zonificación desde GeoSERFOR.
    """
    id_solicitud: int = Field(..., description="ID de la solicitud del Bosque Local")


class ZonificacionItem(BaseModel):
    """
    Item individual de zonificación forestal.
    """
    denominacion: str = Field(..., description="Nombre o denominación de la zona")
    superficie_ha: float = Field(..., description="Superficie en hectáreas")
    porcentaje: float = Field(..., description="Porcentaje respecto al área total")
    geometria: Optional[Dict[str, Any]] = Field(None, description="Geometría GeoJSON para dibujar en mapa")


class ObtenerZonificacionResponse(BaseModel):
    """
    Respuesta del endpoint de obtención de zonificación.
    """
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: Optional[str] = Field(None, description="Mensaje adicional (ej: sin datos)")
    zonificaciones: List[ZonificacionItem] = Field(..., description="Lista de zonificaciones")
    total_superficie_ha: Optional[float] = Field(None, description="Superficie total en hectáreas")
    total_porcentaje: Optional[float] = Field(None, description="Porcentaje total")


# --- API Endpoints ---

@router.post(
    "/bosque-local/registrar",
    summary="Registrar una nueva geometría de Bosque Local",
    description="Registra una geometría (punto, línea o polígono) asociada a una solicitud de Bosque Local, "
                "ejecutando el stored procedure `pa_BosqueLocalGeometria_Registrar`.",
    status_code=201,
    response_model=BosqueLocalResponse
)
def registrar_bosque_local_endpoint(payload: BosqueLocalRequest = Body(...)):
    """
    Endpoint para registrar una nueva geometría de Bosque Local en la base de datos.
    
    - **idSolicitud**: ID de la solicitud asociada
    - **idArchivo**: ID del archivo/documento (opcional)
    - **tipoGeometria**: Tipo de geometría (Punto, Línea, Polígono)
    - **zonaUtm**: Zona UTM (17, 18 o 19)
    - **idDist**: Código UBIGEO del distrito (6 caracteres)
    - **vertice**: Número de vértices de la geometría
    - **sector**: Sector o bloques
    - **nombreCapa**: Nombre descriptivo de la capa
    - **colorCapa**: Color para visualización
    - **codigoSeccion**: Código de sección
    - **geometriaGeoJSON**: Objeto GeoJSON con la geometría
    - **srid**: SRID de la geometría (default: 32718 - UTM zona 18S)
    - **propiedad**: Atributos adicionales en formato JSON (opcional)
    - **idUsuarioRegistro**: ID del usuario que registra
    """
    try:
        id_geometria = registrar_bosque_local(
            engine=engine,
            id_solicitud=payload.idSolicitud,
            id_archivo=payload.idArchivo,
            tipo_geometria=payload.tipoGeometria,
            zona_utm=payload.zonaUtm,
            id_dist=payload.idDist,
            vertice=payload.vertice,
            sector=payload.sector,
            nombre_capa=payload.nombreCapa,
            color_capa=payload.colorCapa,
            codigo_seccion=payload.codigoSeccion,
            geometria_geojson=payload.geometriaGeoJSON,
            srid=payload.srid,
            propiedad=payload.propiedad,
            id_usuario_registro=payload.idUsuarioRegistro
        )

        if id_geometria is None:
            raise HTTPException(
                status_code=500,
                detail="No se pudo obtener el ID de la geometría registrada"
            )

        return {"idBosqueLocalGeometria": id_geometria}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar la geometría: {str(e)}"
        )


@router.get(
    "/bosque-local/listar",
    summary="Listar geometrías de Bosque Local",
    description="Lista todas las geometrías de Bosque Local activas, con filtros opcionales por solicitud, tipo de geometría, sección o distrito.",
    response_model=List[BosqueLocalGeometriaItem]
)
def listar_bosque_local_geometrias_endpoint(
    id_solicitud: Optional[int] = Query(None, description="Filtrar por ID de solicitud"),
    tipo_geometria: Optional[str] = Query(None, description="Filtrar por tipo de geometría (Punto, Línea, Polígono)"),
    codigo_seccion: Optional[str] = Query(None, description="Filtrar por código de sección"),
    id_dist: Optional[str] = Query(None, description="Filtrar por UBIGEO de distrito (6 caracteres)")
):
    """
    Endpoint para listar geometrías de Bosque Local con filtros opcionales.
    
    Los filtros son opcionales y se pueden combinar. Si no se proporciona ningún filtro,
    devuelve todas las geometrías activas.
    """
    try:
        geometrias = listar_bosque_local_geometrias(
            engine=engine,
            id_solicitud=id_solicitud,
            tipo_geometria=tipo_geometria,
            codigo_seccion=codigo_seccion,
            id_dist=id_dist
        )

        return geometrias

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar las geometrías: {str(e)}"
        )


@router.delete(
    "/bosque-local/eliminar/{id_bl_geometria}",
    summary="Eliminar una geometría de Bosque Local",
    description="Realiza el borrado lógico (soft delete) de una geometría de Bosque Local por su ID.",
    status_code=200
)
def eliminar_bosque_local_geometria_endpoint(
    id_bl_geometria: int,
    id_usuario: int = Query(..., description="ID del usuario que realiza la eliminación")
):
    """
    Endpoint para eliminar lógicamente una geometría de Bosque Local.
    
    - **id_bl_geometria**: ID de la geometría a eliminar
    - **id_usuario**: ID del usuario que realiza la acción (para auditoría)
    
    El borrado es lógico: cambia el estado a 'I' (Inactivo) y registra la fecha y usuario.
    """
    try:
        fue_eliminado = eliminar_bosque_local_geometria(
            engine=engine,
            id_bl_geometria=id_bl_geometria,
            id_usuario=id_usuario
        )

        if not fue_eliminado:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró la geometría con ID {id_bl_geometria}."
            )

        return {
            "message": f"Geometría con ID {id_bl_geometria} eliminada exitosamente.",
            "idEliminado": id_bl_geometria
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar la geometría: {str(e)}"
        )


@router.post(
    "/bosque-local/obtener-zonificacion",
    summary="Obtener zonificación forestal desde GeoSERFOR",
    description="""
    Obtiene automáticamente la zonificación u ordenamiento forestal desde el servicio GeoSERFOR
    para el área de un Bosque Local específico.
    
    **IMPORTANTE:** Este endpoint NO guarda en base de datos. Solo consulta GeoSERFOR y retorna
    los resultados CON LA GEOMETRÍA de cada zona para dibujar en el mapa.

    **Proceso:**
    1. Obtiene la geometría del Bosque Local desde la base de datos
    2. Consulta el servicio ArcGIS REST de GeoSERFOR
    3. Filtra las features que intersectan con el área del Bosque Local
    4. Calcula el área de cada zona (hectáreas)
    5. Calcula el porcentaje respecto al área total
    6. Retorna la lista de zonas CON SU GEOMETRÍA para dibujar en el mapa
    """,
    status_code=200,
    response_model=ObtenerZonificacionResponse
)
def obtener_zonificacion_endpoint(payload: ObtenerZonificacionRequest = Body(...)):
    """
    Obtiene la zonificación forestal desde GeoSERFOR y la retorna con geometría para dibujar en el mapa.
    """
    try:
        # 1. Obtener la geometría del Bosque Local desde la BD
        geometrias = listar_bosque_local_geometrias(
            engine=engine,
            id_solicitud=payload.id_solicitud
        )

        if not geometrias:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró un Bosque Local con la solicitud ID {payload.id_solicitud}"
            )

        bosque_local = geometrias[0]
        geometry_geojson = bosque_local.get("geometry_geojson")

        if not geometry_geojson:
            raise HTTPException(
                status_code=400,
                detail="El Bosque Local no tiene una geometría definida"
            )

        # 2. Consultar GeoSERFOR directamente (sin guardar en BD)
        resultado_geoserfor = obtener_zonificacion_geoserfor(
            bosque_local_geometry=geometry_geojson
        )

        if not resultado_geoserfor.get("success"):
            raise HTTPException(
                status_code=500,
                detail=resultado_geoserfor.get("error", "Error al consultar GeoSERFOR")
            )

        zonificaciones = resultado_geoserfor.get("zonificaciones", [])

        if not zonificaciones:
            return ObtenerZonificacionResponse(
                success=True,
                message=resultado_geoserfor.get(
                    "message",
                    "No se encontró información de Zonificación u Ordenamiento Forestal para el área."
                ),
                zonificaciones=[],
                total_superficie_ha=0,
                total_porcentaje=0
            )

        # 3. Construir respuesta incluyendo la geometría para dibujar en el mapa
        zonificaciones_items = [
            ZonificacionItem(
                denominacion=z["denominacion"],
                superficie_ha=z["superficie_ha"],
                porcentaje=z["porcentaje"],
                geometria=z.get("geometria")  # GeoJSON para dibujar en el mapa
            )
            for z in zonificaciones
        ]

        return ObtenerZonificacionResponse(
            success=True,
            zonificaciones=zonificaciones_items,
            total_superficie_ha=resultado_geoserfor.get("total_superficie_ha"),
            total_porcentaje=resultado_geoserfor.get("total_porcentaje")
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener la zonificación: {str(e)}"
        )
