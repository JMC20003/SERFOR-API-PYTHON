# Project Overview

This project is a Python-based web API named "Visor GeoForestal API". It is built using the FastAPI framework and serves as a backend for geospatial analysis and queries related to forestry information, likely for SERFOR (Servicio Nacional Forestal y de Fauna Silvestre) in Peru.

The API provides endpoints for performing geospatial intersections, querying "títulos habilitantes" (enabling titles), and other geoprocessing tasks. It uses a combination of Python libraries for geospatial operations and a Microsoft SQL Server database for data storage and retrieval. A significant portion of the business logic is implemented as stored procedures in the database.

## Key Technologies

*   **Backend Framework:** FastAPI
*   **Programming Language:** Python
*   **Geospatial Libraries:** Shapely, GeoJSON, Pyproj
*   **Database:** Microsoft SQL Server
*   **Database Driver:** pyodbc
*   **ORM/Querying:** SQLAlchemy (used for executing raw SQL and stored procedures)
*   **Containerization:** Docker and Docker Compose

## Architecture

The application follows a modular architecture:

*   **`app/main.py`:** The main entry point of the FastAPI application. It initializes the app and includes the API routers.
*   **`app/apis/v1/`:** Contains the API version 1, with endpoints and schemas.
    *   **`endpoints/`:** Defines the API endpoints and handles request/response validation using Pydantic.
    *   **`schemas/`:** Defines the Pydantic models for data validation.
*   **`app/services/`:** Contains the business logic. The `geo_service.py` is the core of the application, handling geospatial calculations and database interactions.
*   **`app/db/`:** Manages the database connections. `session.py` creates SQLAlchemy engines for connecting to multiple SQL Server databases/schemas.
*   **`app/core/`:** Handles the application's configuration. `config.py` loads environment variables from a `.env` file.
*   **`requirements/`:** Contains the Python dependencies, separated into `base.txt` and `dev.txt`.

# Building and Running

## Development (without Docker)

1.  **Prerequisites:**
    *   Python 3.x
    *   ODBC Driver for SQL Server

2.  **Setup:**
    *   Create a virtual environment: `python -m venv .venv`
    *   Activate the virtual environment.
    *   Install dependencies: `pip install -r requirements/base.txt -r requirements/dev.txt`
    *   Create a `.env` file based on `.env.example` and fill in the database credentials.

3.  **Running:**
    *   Start the development server: `uvicorn app.main:app --reload --port 8000`

## Production (with Docker)

1.  **Prerequisites:**
    *   Docker
    *   Docker Compose

2.  **Setup:**
    *   Create a `.env` file with the necessary environment variables.

3.  **Running:**
    *   Build and run the Docker container in detached mode: `docker-compose -f docker-compose.yml up -d`

# Development Conventions

*   **Modular Design:** The code is organized into modules with a clear separation of concerns (API, services, database).
*   **Dependency Management:** Python dependencies are managed in `requirements/` files.
*   **Configuration:** Application configuration and secrets are managed through environment variables loaded from a `.env` file.
*   **Database Interaction:** The application heavily relies on stored procedures for business logic. The Python code primarily acts as a wrapper to call these stored procedures.
*   **API Documentation:** The API is self-documenting using FastAPI's automatic Swagger UI (`/docs`) and ReDoc (`/redoc`) generation.
*   **Geospatial Handling:** The application uses `shapely` for geometry manipulation, `geojson` for data interchange, and `pyproj` for coordinate transformations.
