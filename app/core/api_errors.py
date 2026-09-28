import re
from fastapi import HTTPException


def clasificar_error_db(exc: Exception) -> str | None:
    """
    Clasifica un error de base de datos (pyodbc/SQLAlchemy/SQL Server)
    y devuelve un mensaje claro y accionable para el usuario final.
    Devuelve None si el error no corresponde a un caso conocido.
    """
    msg = str(exc)
    low = msg.lower()

    if "4060" in msg or "cannot open database" in low:
        return ("El servidor de base de datos respondió, pero no se pudo abrir la base de datos "
                "(puede estar caída, en restauración, o el usuario no tiene permisos sobre ella). "
                "Contacte al administrador de la base de datos.")

    if "18456" in msg or "login failed" in low:
        return ("No se pudo autenticar con la base de datos: el usuario o la contraseña son "
                "incorrectos, o ese usuario no tiene permiso para conectarse. Verifíquelo con "
                "el administrador de la base de datos.")

    if "208" in msg or "invalid object name" in low:
        return ("Error de configuración: la base de datos no contiene la tabla o el procedimiento "
                "esperado. Contacte al área de sistemas.")

    if "im002" in low or "data source name not found" in low or "driver does not exist" in low or "specified driver could not be loaded" in low:
        return ("Configuración de conexión incorrecta: no se encontró el controlador ODBC de "
                "SQL Server en este servidor. Contacte al administrador.")

    if re.search(
        r"communication link failure|cannot connect|network error|connection (was )?closed|"
        r"connection reset|connection refused|unable to connect|not accessible|connection timed out|"
        r"login timeout|timed out|timeout|host is not reachable|server is not reachable|"
        r"server is? down|error: 53|error: 10060|error: 10061|socket|no pudo establecerse",
        low,
    ):
        return ("No se pudo conectar con el servidor de base de datos. Es probable que el servicio "
                "esté caído o que haya un problema de red. Intente nuevamente en unos minutos.")

    return None


def error_db_http(exc: Exception, contexto: str, *, status: int = 500) -> HTTPException:
    """
    Convierte un error de base de datos en un HTTPException con un mensaje claro.
    - exc: la excepción capturada.
    - contexto: acción en curso, p. ej. "registrar la geometría de Bosque Local".
    """
    mensaje = clasificar_error_db(exc)
    if mensaje:
        print(f"❌ Error al {contexto}: {exc}")
        return HTTPException(status_code=status, detail=mensaje)
    return HTTPException(status_code=500, detail=f"Error al {contexto}: {exc}")