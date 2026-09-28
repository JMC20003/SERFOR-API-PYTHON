# Visor GeoForestal API

API para el Visor GeoForestal, que proporciona servicios geoespaciales para la consulta y análisis de datos relacionados con el sector forestal.

## Requisitos Previos

*   Python 3.12.4
*   ODBC Driver for SQL Server

## Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd api-serfor
    ```

2.  **Crear un entorno virtual:**

    ```bash
    python -m venv .venv
    ```

3.  **Activar el entorno virtual:**

    *   **En Windows:**

        ```bash
        .venv\Scripts\activate
        ```

    *   **En macOS y Linux:**

        ```bash
        source .venv/bin/activate
        ```

4.  **Instalar dependencias:**

    ```bash
    pip install -r requirements/base.txt
    pip install -r requirements/dev.txt
    ```

## Configuración

1.  **Crear un archivo `.env`:**

    Cree un archivo `.env` en la raíz del proyecto, basándose en el archivo `.env.example`.

    ```bash
    cp .env.example .env
    ```

2.  **Configurar las variables de entorno:**

    Abra el archivo `.env` y complete las credenciales de la base de datos:

    ```
    DB_SERVER=
    DB_DATABASE=
    DB_USER=
    DB_PASSWORD=
    DB_DATABASE_COBERTURA=
    DB_SERVER_AREA=
    DB_DATABASE_AREA=
    DB_USER_AREA=
    DB_PASSWORD_AREA=
    ```

## Uso

1.  **Iniciar el servidor de desarrollo:**

    ```bash
    uvicorn app.main:app --reload --port 8000
    ```

2.  **Acceder a la documentación de la API:**

    Una vez que el servidor esté en funcionamiento, puede acceder a la documentación interactiva de la API en las siguientes URL:

    *   **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    *   **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Endpoints

La API proporciona los siguientes endpoints para realizar análisis geoespaciales y gestionar datos.

### Pruebas

*   **`GET /api/test-odbc`**
    *   **Descripción:** Prueba la conexión ODBC con la base de datos y devuelve una lista de las bases de datos disponibles.
    *   **Uso:** Ideal para verificar que la configuración del archivo `.env` es correcta y que el servidor de la API puede comunicarse con la base de datos.
    *   **Respuesta Exitosa (200):**
        ```json
        {
          "conectado": true,
          "bases": ["master", "tempdb", "model", "msdb", "su_nombre_de_bd"]
        }
        ```

### Intersección Geoespacial

Estos endpoints permiten realizar análisis de intersección entre un área geográfica definida por un GeoJSON y diversas capas de información.

*   **`POST /api/v1/interseccion`**
    *   **Descripción:** Calcula la intersección entre un GeoJSON de entrada y una tabla específica de la base de datos.
    *   **Parámetros (Cuerpo de la Petición):**
        *   `table` (string): Nombre de la tabla a intersecar, en formato `schema.tabla`.
        *   `geojson` (object): Un objeto GeoJSON (Feature o FeatureCollection) que define el polígono o área de interés.
    *   **Ejemplo de Petición:**
        ```json
        {
          "table": "public.bosques_secos",
          "geojson": {
            "type": "Feature",
            "geometry": {
              "type": "Polygon",
              "coordinates": [[[-79, -5], [-78, -5], [-78, -6], [-79, -6], [-79, -5]]]
            },
            "properties": {}
          }
        }
        ```
    *   **Respuesta Exitosa (200):** Un `FeatureCollection` GeoJSON con los polígonos resultantes de la intersección y sus propiedades (área en hectáreas, etc.).

*   **`POST /api/v1/interseccion/cobertura`**
    *   **Descripción:** Especializado en calcular la intersección con la capa de cobertura vegetal.
    *   **Parámetros:** Un GeoJSON en el cuerpo de la petición.
    *   **Respuesta:** Similar a `/interseccion`, devuelve un `FeatureCollection` con los resultados.

*   **`POST /api/v1/interseccion/multiple`**
    *   **Descripción:** Realiza una intersección del GeoJSON de entrada contra un conjunto predefinido de capas importantes (ej. áreas protegidas, concesiones, etc.).
    *   **Parámetros:** Un GeoJSON en el cuerpo de la petición.
    *   **Respuesta:** Un `FeatureCollection` que agrega los resultados de todas las intersecciones.

*   **`POST /api/v1/interseccion/dominio`**
    *   **Descripción:** Calcula la intersección con la capa de dominio, útil para análisis de tenencia de tierras.
    *   **Parámetros:** Un GeoJSON en el cuerpo de la petición.
    *   **Respuesta:** `FeatureCollection` con los resultados de la intersección.

### Títulos Habilitantes

Endpoints para consultar información sobre Títulos Habilitantes (TH).

*   **`GET /api/v1/titulo-habilitante-area?tituloHabilitante={codigo}`** (recomendado, slash-safe)
    *   **Descripción:** Busca un Título Habilitante por su código o nombre parcial y devuelve las áreas geoespaciales asociadas. El código se envía como query param, por lo que soporta códigos con `/` (ej. `17-MAD-TAM/CON-PFDM-2019-018` → `tituloHabilitante=17-MAD-TAM%2FCON-PFDM-2019-018`).
    *   **Parámetros (Query):**
        *   `tituloHabilitante` (string, obligatorio): Código o nombre para la búsqueda.
    *   **Respuesta Exitosa (200):** Un `FeatureCollection` GeoJSON con la geometría del título encontrado.

*   **`GET /api/v1/titulo-habilitante-area/{th_area}`** (legacy, solo códigos sin `/`)
    *   **Descripción:** Busca un Título Habilitante por su código o nombre parcial y devuelve las áreas geoespaciales asociadas. Solo funciona con códigos que no contengan `/`; para códigos con `/` usar el endpoint con query param.
    *   **Parámetros (URL):**
        *   `th_area` (string): Código o nombre para la búsqueda.
    *   **Respuesta Exitosa (200):** Un `FeatureCollection` GeoJSON con la geometría del título encontrado.

*   **`POST /api/v1/titulo-habilitante`**
    *   **Descripción:** Obtiene la geometría de un Título Habilitante a partir de su código exacto.
    *   **Parámetros (Cuerpo de la Petición):**
        *   `codigo_th` (string): Código exacto del título.
    *   **Respuesta:** `FeatureCollection` con la geometría.

### Geoprocesos

Funciones de utilidad para análisis de geometrías.

*   **`POST /api/v1/calculate-area/`**
    *   **Descripción:** Calcula el área en hectáreas de un único `Feature` GeoJSON.
    *   **Parámetros:** Un objeto `Feature` GeoJSON.
    *   **Respuesta:** Un JSON con el área calculada.

*   **`POST /api/v1/analyze-geojson/`**
    *   **Descripción:** Analiza una `FeatureCollection` completa, extrayendo los vértices y calculando el área total para cada `Feature`.
    *   **Parámetros:** Un objeto `FeatureCollection` GeoJSON.
    *   **Respuesta:** Una lista de resultados con vértices y áreas por cada `Feature`.

### Almacenamiento Temporal

Estos endpoints permiten guardar y recuperar un estado temporal de la aplicación, útil para interfaces de usuario interactivas.

*   **`POST /api/v1/temporal-data`**
    *   **Descripción:** Guarda un estado (JSON) en un archivo temporal en el servidor. Cada llamada sobrescribe el contenido anterior.
    *   **Parámetros:** Cualquier estructura JSON que represente el estado a guardar.

*   **`GET /api/v1/temporal-data`**
    *   **Descripción:** Recupera el estado guardado en el archivo temporal.

### Capas Guardadas (Shapes)

Permite persistir en la base de datos capas GeoJSON asociadas a un "Plan de Manejo".

*   **`POST /api/v1/capas`**
    *   **Descripción:** Guarda una nueva capa GeoJSON en la base de datos.
    *   **Parámetros:**
        *   `idPlanManejo` (int): ID del plan de manejo al que se asocia la capa.
        *   `nombreCapa` (string): Nombre descriptivo de la capa.
        *   `datosGeoJSON` (object): El contenido GeoJSON de la capa.
        *   `zona` (string): Zona UTM.

*   **`GET /api/v1/capas/{id_plan_manejo}`**
    *   **Descripción:** Obtiene todas las capas guardadas para un `idPlanManejo` específico.

*   **`DELETE /api/v1/capas/{capa_id}`**
    *   **Descripción:** Elimina una capa de la base de datos usando su ID único.

### Secciones de Formulario

Endpoints para guardar y recuperar datos de secciones de formularios dinámicos.

*   **`POST /api/v1/formulario/seccion`**
    *   **Descripción:** Guarda o actualiza los datos de una sección específica de un formulario, asociado a un Título Habilitante.
    *   **Parámetros:**
        *   `tituloHabilitante` (string): Código del TH.
        *   `tipo` (string): Tipo de formulario.
        *   `seccion` (string): Nombre de la sección.
        *   `datos` (any): Contenido JSON de la sección.

*   **`GET /api/v1/formulario/seccion?tituloHabilitante={codigo}&tipo={tipo}`** (recomendado, slash-safe)
    *   **Descripción:** Recupera todas las secciones y sus datos para un Título Habilitante y tipo de formulario específicos. El código se envía como query param, por lo que soporta códigos con `/`.
    *   **Parámetros (Query):**
        *   `tituloHabilitante` (string, obligatorio): Código del TH.
        *   `tipo` (string, obligatorio): Tipo de formulario.

*   **`GET /api/v1/formulario/seccion/{titulo_habilitante}/{tipo}`** (legacy, solo códigos sin `/`)
    *   **Descripción:** Recupera todas las secciones y sus datos para un Título Habilitante y tipo de formulario específicos. Solo funciona con códigos que no contengan `/`; para códigos con `/` usar el endpoint con query params.



## Despliegue en Producción (Ubuntu)

Esta guía describe los pasos para desplegar la API en un servidor Ubuntu en un entorno de producción.

### 1. Requisitos del Servidor

Primero, actualice el sistema e instale las dependencias necesarias.

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv nginx curl
```

### 2. Instalar ODBC Driver de SQL Server

La aplicación necesita el driver ODBC de Microsoft para conectarse a la base de datos SQL Server.

```bash
# Registrar el repositorio de Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Instalar el driver y herramientas
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Configuración de la Aplicación

1.  **Clonar el código fuente:**

    ```bash
    git clone <URL_DEL_REPOSITORIO> /var/www/api-serfor
    cd /var/www/api-serfor
    ```

2.  **Crear y activar el entorno virtual:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instalar dependencias de Python:**

    Asegúrese de instalar `gunicorn` para el servidor de producción.

    ```bash
    pip install -r requirements/base.txt
    pip install gunicorn
    ```

4.  **Configurar el archivo `.env`:**

    Cree y edite el archivo `.env` con las credenciales de la base de datos de producción.

    ```bash
    cp .env.example .env
    nano .env
    ```

### 4. Configurar Gunicorn y Systemd

Para que la API se ejecute de forma robusta, se recomienda usar `gunicorn` como servidor ASGI y `systemd` para gestionarlo como un servicio.

1.  **Crear un archivo de servicio de `systemd`:**

    ```bash
    sudo nano /etc/systemd/system/api-serfor.service
    ```

2.  **Añadir la siguiente configuración:**

    Asegúrese de reemplazar `<su_usuario>` con el usuario que ejecutará la aplicación (puede ser `www-data` o un usuario dedicado).

    ```ini
    [Unit]
    Description=Gunicorn instance for api-serfor
    After=network.target

    [Service]
    User=<su_usuario>
    Group=www-data
    WorkingDirectory=/var/www/api-serfor
    EnvironmentFile=/var/www/api-serfor/.env
    ExecStart=/var/www/api-serfor/.venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000

    [Install]
    WantedBy=multi-user.target
    ```

3.  **Iniciar y habilitar el servicio:**

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start api-serfor
    sudo systemctl enable api-serfor
    ```

    Puede verificar el estado del servicio con `sudo systemctl status api-serfor`.

### 5. Configurar Nginx como Reverse Proxy

Nginx actuará como intermediario entre las peticiones de los clientes y Gunicorn.

1.  **Crear un archivo de configuración de Nginx:**

    ```bash
    sudo nano /etc/nginx/sites-available/api-serfor
    ```

2.  **Añadir la configuración del proxy reverso:**

    Reemplace `su-dominio.com` por el dominio o la IP de su servidor.

    ```nginx
    server {
        listen 80;
        server_name su-dominio.com;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

3.  **Habilitar el sitio y reiniciar Nginx:**

    ```bash
    sudo ln -s /etc/nginx/sites-available/api-serfor /etc/nginx/sites-enabled
    sudo nginx -t  # Probar la configuración
    sudo systemctl restart nginx
    ```

### 6. Configurar el Firewall (UFW)

Asegúrese de que el firewall permita el tráfico web.

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Con estos pasos, la API estará desplegada en su servidor Ubuntu, ejecutándose de forma segura y gestionada como un servicio.
