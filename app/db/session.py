from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from app.core.config import (
    DB_SERVER,
    DB_DATABASE,
    DB_USER,
    DB_PASSWORD,
    DB_DATABASE_COBERTURA,
    DB_SERVER_AREA,
    DB_DATABASE_AREA,
    DB_USER_AREA,
    DB_PASSWORD_AREA,
    DRIVER_ODBC
)
DB_PORT = 1433
# 🎯 SQLAlchemy URL
connection_url = URL.create(
    "mssql+pyodbc",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_SERVER,
    port=DB_PORT,
    database=DB_DATABASE,
    query={
        "driver": DRIVER_ODBC,
        "TrustServerCertificate": "yes",
        "Encrypt": "no"
    }
)
engine = create_engine(connection_url, echo=False)

# Segundo engine para cobertura vegetal
connection_url_cobertura = URL.create(
    "mssql+pyodbc",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_SERVER,
    port=DB_PORT,
    database=DB_DATABASE_COBERTURA,
    query={
        "driver": DRIVER_ODBC,
        "TrustServerCertificate": "yes",
        "Encrypt": "no"
    }
)
engine_cobertura = create_engine(connection_url_cobertura, echo=False)

# Tercer engine para titulo habilitante area
connection_url_titulohabilitante_area = URL.create(
    "mssql+pyodbc",
    username=DB_USER_AREA,
    password=DB_PASSWORD_AREA,
    host=DB_SERVER_AREA,
    port=DB_PORT,
    database=DB_DATABASE_AREA,
    query={
        "driver": DRIVER_ODBC,
        "TrustServerCertificate": "yes",
        "Encrypt": "no"
    }
)
engine_titulohabilitante_area = create_engine(connection_url_titulohabilitante_area, echo=False)
