from fastapi import APIRouter, Body, HTTPException, Query
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



def _obtener_secciones(titulo_habilitante: str, tipo: str):
    try:
        return geo_service.obtener_secciones_formulario(
            engine=engine,
            titulo_habilitante=titulo_habilitante,
            tipo=tipo
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener secciones: {str(e)}")

@router.get(
    "/formulario/seccion",
    summary="Obtener todas las secciones de un formulario",
    description="Recupera las secciones guardadas de un Título Habilitante y tipo. El código se envía como query param (slash-safe): ?tituloHabilitante=17-MAD-TAM%2FCON-PFDM-2019-018&tipo=CON-PFDM",
    response_model=List[SeccionFormularioResponse]
)
def obtener_seccion(tituloHabilitante: str = Query(..., description="Código del Título Habilitante."), tipo: str = Query(..., description="Tipo de formulario.")):
    """
    Obtiene todas las secciones de un formulario a partir del código del TH y tipo.

    - **tituloHabilitante**: Código del TH (query param, soporta `/`).
    - **tipo**: Tipo de formulario.
    """
    return _obtener_secciones(tituloHabilitante, tipo)

@router.get(
    "/formulario/seccion/{titulo_habilitante}/{tipo}",
    summary="Obtener todas las secciones de un formulario",
    description="Recupera las secciones guardadas de un Título Habilitante y tipo. Ruta legacy: no soporta códigos con `/`; usar query params en esos casos.",
    response_model=List[SeccionFormularioResponse]
)
def obtener_secciones(titulo_habilitante: str, tipo: str):
    """
    Obtiene todas las secciones de un formulario. Ruta legacy: el código con `/` no funciona; usar `?tituloHabilitante=&tipo=`.
    """
    return _obtener_secciones(titulo_habilitante, tipo)
