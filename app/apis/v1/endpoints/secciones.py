from fastapi import APIRouter, Body, HTTPException
from typing import List
from app.services import geo_service
from app.db.session import engine
from pydantic import BaseModel
from typing import Any, Dict


router = APIRouter()

# app/schemas/formulario.py

class SeccionFormularioPayload(BaseModel):
    tituloHabilitante: str
    tipo: str
    seccion: str
    datos: Any

class SeccionFormularioResponse(BaseModel):
    seccion: str
    datos: Any
    fechaRegistro: str

@router.post(
    "/formulario/seccion",
    summary="Guardar o actualizar una sección de formulario",
    status_code=201
)
def guardar_seccion(payload: SeccionFormularioPayload = Body(...)):
    try:
        success = geo_service.guardar_seccion_formulario(
            engine=engine,
            titulo_habilitante=payload.tituloHabilitante,
            tipo=payload.tipo,
            seccion=payload.seccion,
            datos=payload.datos
        )

        return { "message": "Sección guardada correctamente", "success": success }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar sección: {str(e)}")



@router.get(
    "/formulario/seccion/{titulo_habilitante}/{tipo}",
    summary="Obtener todas las secciones de un formulario",
    response_model=List[SeccionFormularioResponse]
)
def obtener_secciones(titulo_habilitante: str, tipo: str):
    try:
        data = geo_service.obtener_secciones_formulario(
            engine=engine,
            titulo_habilitante=titulo_habilitante,
            tipo=tipo
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener secciones: {str(e)}")
