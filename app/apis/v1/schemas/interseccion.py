from pydantic import BaseModel

class InterseccionRequest(BaseModel):
    table: str
    geojson: dict
