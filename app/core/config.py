import os
from dotenv import load_dotenv

load_dotenv()

# 🚀 Config FastAPI
DB_SERVER = os.getenv('DB_SERVER')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = 1433
DB_DATABASE_COBERTURA = os.getenv('DB_DATABASE_COBERTURA')
# Configuración DB Titulo Habilitante Area
DB_SERVER_AREA = os.getenv('DB_SERVER_AREA')
DB_DATABASE_AREA = os.getenv('DB_DATABASE_AREA')
DB_USER_AREA = os.getenv('DB_USER_AREA')
DB_PASSWORD_AREA = os.getenv('DB_PASSWORD_AREA')
DRIVER_ODBC = os.getenv('DRIVER_ODBC')
