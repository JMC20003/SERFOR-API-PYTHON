# Stage 1: Builder - Instala dependencias de compilación y de Python
FROM python:3.12-slim as builder

# Variable de entorno para evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias del sistema para compilar pyodbc
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia los requerimientos e instala las dependencias de Python
COPY ./requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements/base.txt
RUN pip install pyproj
# ---

# Stage 2: Production - Imagen final optimizada
FROM python:3.12-slim

# Variable de entorno para evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instala el driver Microsoft ODBC 18 para SQL Server (para Debian 12)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg curl \
    libgssapi-krb5-2 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && ldconfig \
    && apt-get purge -y --auto-remove gnupg curl \
    && rm -rf /var/lib/apt/lists/*

# Crea un grupo y usuario no-root para ejecutar la aplicación
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copia los paquetes de Python y los ejecutables instalados desde la etapa 'builder'
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copia el código de la aplicación
COPY ./app /app/app

# Asigna la propiedad del directorio de la app al nuevo usuario
RUN chown -R appuser:appgroup /app

# Cambia al usuario no-root
USER appuser

# Expone el puerto en el que corre la aplicación
EXPOSE 8000

# Comando para iniciar la aplicación con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
