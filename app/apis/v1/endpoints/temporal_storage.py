import json
import os
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Any, Dict, Optional

router = APIRouter()

# --- Configuración de ruta segura para Docker y local ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(os.path.dirname(BASE_DIR), "storage")
TEMPORAL_FILE_PATH = os.path.join(STORAGE_DIR, "temporal_data.json")

# --- Pydantic Models ---
# Modelos actualizados para coincidir con el nuevo payload del frontend.

class LayerData(BaseModel):
    visible: Optional[bool] = None
    layer: Optional[Dict[str, Any]] = None

class Poligonos(BaseModel):
    areaUmf: Optional[LayerData] = None
    bloques: Optional[LayerData] = None
    fisiografia: Optional[LayerData] = None
    ordenamiento: Optional[LayerData] = None
    parcelas: Optional[LayerData] = None

class Vertices(BaseModel):
    areaUmf: Optional[LayerData] = None
    bloques: Optional[LayerData] = None
    parcelas: Optional[LayerData] = None

class FileStates(BaseModel):
    poligonos: Optional[Poligonos] = None
    vertices: Optional[Vertices] = None

class TemporalDataPayload(BaseModel):
    idPlanManejo: Optional[int] = None
    fileStates: Optional[FileStates] = None


# --- API Endpoints ---
 
@router.post(
    "/temporal-data",
    summary="Guardar datos temporales de estado",
    description="Guarda datos temporales de estado de la interfaz. El payload es flexible, permitiendo enviar un objeto parcial con solo los datos que se deseen almacenar. Cada llamada sobrescribe el contenido del archivo temporal."
)
def save_temporal_data(payload: TemporalDataPayload = Body(...)):
    """
    Guarda el payload flexible recibido en un archivo JSON temporal.
    El payload puede ser un objeto parcial. Cada llamada sobrescribe el archivo.
    """
    try:
        # Asegurarse de que el directorio de almacenamiento exista.
        os.makedirs(os.path.dirname(TEMPORAL_FILE_PATH), exist_ok=True)

        data_to_save = payload.model_dump()

        with open(TEMPORAL_FILE_PATH, "w") as f:
            json.dump(data_to_save, f, indent=4)

        return {"message": "Datos guardados exitosamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar los datos: {str(e)}")

@router.get(
    "/temporal-data",
    summary="Obtener datos temporales de polígonos",
    description="Lee y devuelve el contenido del archivo JSON temporal."
)
def get_temporal_data():
    """
    Obtiene los datos desde el archivo JSON temporal.
    """
    try:
        with open(TEMPORAL_FILE_PATH, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No se encontraron datos temporales. Por favor, haga un POST primero.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer los datos: {str(e)}")
