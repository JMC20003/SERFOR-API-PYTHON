from fastapi import APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services import geo_service
from app.db.session import engine # Importar el engine principal

router = APIRouter()

# --- Pydantic Models ---

class CapaGuardadaPayload(BaseModel):
    """Payload para guardar una nueva capa."""
    idPlanManejo: int
    nombreCapa: str
    datosGeoJSON: Dict[str, Any]
    zona:str

class CapaGuardadaResponse(BaseModel):
    """Payload de respuesta para una capa guardada."""
    CapaID: int
    idPlanManejo: int
    NombreCapa: str
    DatosGeoJSON: Dict[str, Any]
    Zona: str | None = None


# --- API Endpoints ---

@router.post(
    "/capas",
    summary="Guardar una nueva capa GeoJSON",
    description="Guarda de forma permanente una capa (shapefile convertido a GeoJSON) en la base de datos, asociándola a un idPlanManejo.",
    status_code=201
)
def guardar_capa_en_db(payload: CapaGuardadaPayload = Body(...)):
    """
    Endpoint para persistir una capa en la base de datos.
    """
    try:
        # Llama a la función de servicio para ejecutar el stored procedure
        nuevo_id = geo_service.guardar_capa(
            engine=engine, # Pasar el engine
            id_plan_manejo=payload.idPlanManejo,
            nombre_capa=payload.nombreCapa,
            datos_geojson=payload.datosGeoJSON,
            zona=payload.zona
        )
        return {"message": "Capa guardada exitosamente", "nuevoCapaID": nuevo_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la capa: {str(e)}")

@router.get(
    "/capas/{id_plan_manejo}",
    summary="Obtener todas las capas guardadas para un Plan de Manejo",
    description="Recupera todas las capas GeoJSON asociadas a un idPlanManejo específico desde la base de datos.",
    response_model=List[CapaGuardadaResponse]
)
def obtener_capas_de_db(id_plan_manejo: int):
    """
    Endpoint para obtener todas las capas persistidas para un idPlanManejo.
    """
    try:
        capas = geo_service.obtener_capas_por_plan(
            engine=engine, # Pasar el engine
            id_plan_manejo=id_plan_manejo
        )
        if not capas:
            return []
        return capas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las capas: {str(e)}")

@router.delete(
         "/capas/{capa_id}",
         summary="Eliminar una capa guardada por su ID",
         description="Elimina de forma permanente una capa de la base de datos usando su ID único.",
         status_code=200
     )
def eliminar_capa_de_db(capa_id: int):
    """
    Endpoint para eliminar una capa persistida por su ID.
    """
    try:
        fue_eliminado = geo_service.eliminar_capa(
            engine=engine,
            capa_id=capa_id
        )
   
        if not fue_eliminado:
            raise HTTPException(status_code=404, detail=f"No se encontró la capa con ID {capa_id}.")
   
        return {"message": f"Capa con ID {capa_id} eliminada exitosamente."}
    except HTTPException as http_exc:
            # Re-lanzar la excepción HTTP para que FastAPI la maneje
            raise http_exc
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar la capa: {str(e)}")