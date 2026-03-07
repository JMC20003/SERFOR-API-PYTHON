from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.apis.v1.endpoints import interseccion, titulo_habilitante, geoprocess, temporal_storage, capas_guardadas, secciones, unidades_aprovechamiento

app = FastAPI(
    title="Visor GeoForestal API",
    version="1.0.0",
    description="""
    API para el Visor GeoForestal, que proporciona servicios geoespaciales
    para la consulta y análisis de datos relacionados con el sector forestal.
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interseccion.router, prefix="/api/v1", tags=["Interseccion"])
app.include_router(titulo_habilitante.router, prefix="/api/v1", tags=["Titulo Habilitante"])
app.include_router(geoprocess.router, prefix="/api/v1", tags=["Geoprocess"])
app.include_router(temporal_storage.router, prefix="/api/v1", tags=["Temporal Data"])
app.include_router(capas_guardadas.router, prefix="/api/v1", tags=["Capas Guardadas"])
app.include_router(secciones.router, prefix="/api/v1", tags=["Guardar Secciones"])
app.include_router(unidades_aprovechamiento.router, prefix="/api/v1", tags=["Unidades de Aprovechamiento"])

@app.get("/api/test-odbc")
def test_odbc():
    from app.db.session import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sys.databases")).fetchall()
            return {"conectado": True, "bases": [row[0] for row in result]}
    except Exception as e:
        print("❌ Test ODBC error:", e)
        raise HTTPException(status_code=500, detail="Error al conectar ODBC")
