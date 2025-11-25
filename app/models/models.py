from pydantic import BaseModel
from typing import Dict, Any, List

class Geometry(BaseModel):
    type: str
    coordinates: list

class Feature(BaseModel):
    type: str
    geometry: Geometry
    properties: Dict[str, Any]

class FeatureCollection(BaseModel):
    type: str
    features: List[Feature]