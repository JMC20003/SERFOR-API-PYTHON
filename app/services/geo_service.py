from shapely import wkt as wkt_lib
from shapely.geometry import mapping, shape as geom_shape
from shapely.ops import unary_union, transform
import geojson
from sqlalchemy import text
""""
from pyproj import Transformer, CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
"""
import json

def guardar_seccion_formulario(engine, titulo_habilitante: str, tipo: str, seccion: str, datos: dict):
    """
    Ejecuta el SP sp_GuardarSeccionFormulario para guardar o actualizar una sección JSON.
    """

    datos_json = json.dumps(datos)

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                EXEC sp_GuardarSeccionFormulario 
                    @TituloHabilitante = :titulo,
                    @Tipo = :tipo,
                    @Seccion = :seccion,
                    @Datos = :datos;
            """),
            {
                "titulo": titulo_habilitante,
                "tipo": tipo,
                "seccion": seccion,
                "datos": datos_json
            }
        )

        row = result.fetchone()
        conn.commit()

        if row:
            return row[0]  # el SP retorna "1 AS Success"
        return None


def obtener_secciones_formulario(engine, titulo_habilitante: str, tipo: str):
    """
    Ejecuta el SP sp_ObtenerSeccionesFormulario
    y devuelve todas las filas con su JSON deserializado.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                EXEC sp_ObtenerSeccionesFormulario 
                    @TituloHabilitante = :titulo,
                    @Tipo = :tipo;
            """),
            {
                "titulo": titulo_habilitante,
                "tipo": tipo
            }
        )

        filas = []
        for row in result.fetchall():
            filas.append({
                "seccion": row.Seccion,
                "datos": json.loads(row.Datos),
                "fechaRegistro": str(row.FechaRegistro)
            })
        
        return filas



def guardar_capa(engine,id_plan_manejo: int, nombre_capa: str, datos_geojson: dict, zona:str):
    """
    Ejecuta el stored procedure para guardar una capa GeoJSON en la base de datos.
    """
    # Convertir el diccionario de GeoJSON a un string JSON
    datos_geojson_str = json.dumps(datos_geojson)

    with engine.connect() as conn:
        result = conn.execute(text("""
            EXEC dbo.sp_GuardarCapa
                @idPlanManejo = :id_plan_manejo,
                @NombreCapa = :nombre_capa,
                @DatosGeoJSON = :datos_geojson,
                @Zona = :zona;
        """), {
            "id_plan_manejo": id_plan_manejo,
            "nombre_capa": nombre_capa,
            "datos_geojson": datos_geojson_str,
            "zona": zona
        })
        
        # Leer el resultado primero
        row = result.fetchone()
        # Confirmar la transacción para que los datos se guarden
        conn.commit()

        # Opcional: Devolver el ID de la nueva capa si el SP lo retorna
        if row:
            return row[0]
        return None

def obtener_capas_por_plan(engine,id_plan_manejo: int):
    """
    Ejecuta el stored procedure para obtener todas las capas de un plan de manejo.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            EXEC dbo.sp_ObtenerCapasPorPlan @idPlanManejo = :id_plan_manejo;
        """), {"id_plan_manejo": id_plan_manejo})

        columns = result.keys()
        capas = []
        for row in result:
            row_dict = dict(zip(columns, row))
            
            # Convertir el string JSON de la BD a un diccionario
            if 'DatosGeoJSON' in row_dict and isinstance(row_dict['DatosGeoJSON'], str):
                row_dict['DatosGeoJSON'] = json.loads(row_dict['DatosGeoJSON'])
            
            capas.append(row_dict)
            
        return capas

def eliminar_capa(engine, capa_id: int) -> bool:
    """
    Ejecuta el stored procedure para eliminar una capa por su ID.
    Devuelve True si se eliminó correctamente, False si no se encontró.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                EXEC dbo.sp_EliminarCapa @CapaID = :capa_id;
            """), {"capa_id": capa_id})
            
            # Leer el resultado antes del commit
            row = result.fetchone()
            
            # Confirmar la transacción
            conn.commit()
            
            # Evaluar la respuesta del stored procedure
            if row and row[0] == 1:
                return True
            else:
                return False

    except Exception as e:
        print("Error al eliminar la capa:", e)
        return False




def procesar_interseccion(engine, schema, table, wkt_geom):
    with engine.connect() as conn:
        result = conn.execute(text("""
            EXEC dbo.usp_InterseccionValidation 
                @schema_name = :schema_name, 
                @table_name = :table_name, 
                @wkt_geom = :wkt_geom, 
                @wkt_srid = :wkt_srid;
        """), {
            "schema_name": schema,
            "table_name": table,
            "wkt_geom": wkt_geom,
            "wkt_srid": 4326
        })

        columns = result.keys()
        features = []
        for row in result:
            props = dict(zip(columns, row))
            geom = wkt_lib.loads(props['wkt_interseccion'])
            features.append(geojson.Feature(
                geometry=geom,
                properties={
                    "id": props.get("feature_id"),
                    "hectareas": props.get("hectareas"),
                    "km2": props.get("kilometros_cuadrados"),
                    "srid": props.get("srid_resultado")
                }
            ))

        return geojson.FeatureCollection(features)

def procesar_interseccion_cobertura(engine, wkt_geom):
    with engine.connect() as conn:
        result = conn.execute(text("""
            EXEC usuide.usp_InterseccionCoberturaVegetal 
                @wkt_geom = :wkt_geom, 
                @wkt_srid = :wkt_srid;
        """), {
            "wkt_geom": wkt_geom,
            "wkt_srid": 4326
        })

        columns = result.keys()
        features = []
        for row in result:
            props = dict(zip(columns, row))
            geometry = wkt_lib.loads(props['wkt_interseccion'])
            features.append(geojson.Feature(
                geometry=geometry,
                properties={
                    "id": props.get("feature_id"),
                    "tipo_bosque": props.get("tipo_bosque"),
                    "hectareas": props.get("hectareas"),
                    "km2": props.get("kilometros_cuadrados"),
                    "srid": props.get("srid_resultado")
                }
            ))

        return geojson.FeatureCollection(features)

def buscar_titulo_habilitante(engine, codigo: str):
    """
    Paso 1: Buscar título habilitante por código (LIKE).
    Devuelve el registro encontrado (dict) o None.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT TOP 1 NU_ID_TITULOHABILITANTE, TX_TITULOHABILITANTE, TX_DEPARTAMENTO_TH,
            TX_PROVINCIA_TH, TX_DISTRITO_TH
            FROM SERFOR_BDMCSNIFFS_QA3.[TituloHabilitante].[T_MVC_TITULOHABILITANTE]
            WHERE TX_TITULOHABILITANTE LIKE :codigo
        """), {"codigo": f"%{codigo}%"})
        
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None

def obtener_titulo_habilitante_area(engine, nu_id_titulohabilitante: int, department: str, province: str, district: str):
    """
    Paso 2: Buscar áreas vinculadas a un título habilitante.
    Retorna también los vértices en UTM y el área total en hectáreas.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                NU_ID_TITULOHABILITANTE_AREA,
                NU_ID_TITULOHABILITANTE,
                NU_SUPERFICIE,
                NU_SUPERFICIE_APROBADA,
                TX_NOMBRE_CAPA,
                TX_UBIGEO,
                TX_GEOMETRY.STAsText() as Shape_WKT
            FROM SERFOR_BDMCSNIFFS_QA3.[TituloHabilitante].[T_MVD_TITULOHABILITANTE_AREA]
            WHERE NU_ID_TITULOHABILITANTE = :nu_id
        """), {"nu_id": nu_id_titulohabilitante})

        columns = result.keys()
        features = []
        total_area_ha = 0.0

        # Transformador para mostrar geometría en EPSG:4326
        transformer_to_wgs84 = Transformer.from_crs("EPSG:32718", "EPSG:4326", always_xy=True)

        for row in result:
            row_dict = dict(zip(columns, row))

            clean_props = {
                k: v for k, v in row_dict.items()
                if not isinstance(v, bytes) and k != "Shape_WKT"
            }
            clean_props["TX_DEPARTAMENTO_TH"] = department
            clean_props["TX_PROVINCIA_TH"] = province
            clean_props["TX_DISTRITO_TH"] = district

            geometry = None
            vertices_utm = []
            if row_dict.get("Shape_WKT"):
                try:
                    # Geometría original en UTM
                    geom_utm = wkt_lib.loads(row_dict["Shape_WKT"])

                    # Calcular área en hectáreas directamente en UTM
                    area_ha = geom_utm.area / 10000.0
                    total_area_ha += area_ha
                    clean_props["AREA_HA"] = round(area_ha, 4)

                    # Obtener vértices en UTM
                    if geom_utm.geom_type == "Polygon":
                        for x, y in list(geom_utm.exterior.coords):
                            vertices_utm.append([round(x, 4), round(y, 4)])
                    elif geom_utm.geom_type == "MultiPolygon":
                        for poly in geom_utm.geoms:
                            for x, y in list(poly.exterior.coords):
                                vertices_utm.append([round(x, 4), round(y, 4)])

                    # Convertir geometría a WGS84 para interoperabilidad
                    geom_wgs84 = transform(transformer_to_wgs84.transform, geom_utm)
                    geometry = mapping(geom_wgs84)

                except Exception as e:
                    print(f"❌ Error al convertir WKT: {e}")
            clean_props["vertices_utm"] = vertices_utm
            if geometry:
                features.append({
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": clean_props,
                })

        return {
            "type": "FeatureCollection",
            "codigo": nu_id_titulohabilitante,
            "features": features,
            "total_area_ha": round(total_area_ha, 4)   # área total en hectáreas
        }

def procesar_interseccion_multiple(engine, wkt_geom):
    with engine.connect() as conn:
        result = conn.execute(text("""
            EXEC usuide.usp_InterseccionMultiple 
                @wkt_geom = :wkt_geom, 
                @wkt_srid = :wkt_srid;
        """), {
            "wkt_geom": wkt_geom,
            "wkt_srid": 4326
        })

        columns = result.keys()
        features = []

        for row in result:
            props = dict(zip(columns, row))
            try:
                geometry = wkt_lib.loads(props['wkt_interseccion'])
            except Exception as e:
                print(f"⚠️ Error al convertir WKT a geometría: {e}")
                geometry = None

            features.append(geojson.Feature(
                geometry=geometry,
                properties={
                    "tabla_origen": props.get("tabla_origen"),
                    "id": props.get("feature_id"),
                    "hectareas": props.get("hectareas"),
                    "km2": props.get("kilometros_cuadrados"),
                    "srid": props.get("srid_resultado")
                }
            ))

        return geojson.FeatureCollection(features)

def procesar_interseccion_dominio(engine, wkt_geom):
    with engine.connect() as conn:
        result = conn.execute(text("""
            EXEC usuide.usp_InterseccionDominio 
                @wkt_geom = :wkt_geom, 
                @wkt_srid = :wkt_srid;
        """), {
            "wkt_geom": wkt_geom,
            "wkt_srid": 4326
        })

        columns = result.keys()
        intersecciones = []

        for row in result:
            props = dict(zip(columns, row))

            estado = props.get("ESTADO_INTERSECCION", False)
            medida = props.get("MEDIDA", 0.0)
            nombre_capa = props.get("NOMBRE_CAPA")
            wkt_geom = props.get("GEOMETRIA")

            try:
                geometry = wkt_lib.loads(wkt_geom) if wkt_geom else None
            except Exception as e:
                print(f"⚠️ Error al convertir WKT a geometría: {e}")
                geometry = None

            intersecciones.append(geojson.Feature(
                geometry=geometry,
                properties={
                    "nombre_capa": nombre_capa,
                    "estado_interseccion": estado,
                    "medida": medida
                }
            ))

        return geojson.FeatureCollection(intersecciones)

def obtener_titulo_habilitante(engine, codigo):
    with engine.connect() as conn:
        result = conn.execute(text("""
            EXEC sde.TituloHabilitante @codigo_th = :codigo_th
        """), {"codigo_th": codigo})

        columns = result.keys()
        features = []

        for row in result:
            row_dict = dict(zip(columns, row))

            clean_props = {
                k: v for k, v in row_dict.items()
                if not isinstance(v, bytes) and k != "Shape_WKT"
            }

            geometry = None
            if "Shape_WKT" in row_dict and row_dict["Shape_WKT"]:
                try:
                    geometry = mapping(wkt_lib.loads(row_dict["Shape_WKT"]))
                except Exception as e:
                    print(f"❌ Error al convertir WKT: {e}")

            if geometry:
                features.append({
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": clean_props
                })

        return {
            "type": "FeatureCollection",
            "codigo": codigo,
            "features": features
        }

def get_area_and_percentage(feature):
    """
    Calculates the area of a GeoJSON geometry in hectares after converting it to the appropriate UTM zone.
    """
    geom = geom_shape(feature.geometry.model_dump())

    # Get the centroid of the geometry to determine the UTM zone
    centroid = geom.centroid
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree=centroid.x,
            south_lat_degree=centroid.y,
            east_lon_degree=centroid.x,
            north_lat_degree=centroid.y,
        ),
    )
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)

    # Define the transformation from WGS84 to UTM
    transformer = Transformer.from_crs(CRS("EPSG:4326"), utm_crs, always_xy=True)

    # Transform the geometry to UTM
    geom_transformed = transform(transformer.transform, geom)

    # Calculate the area in square meters and convert to hectares
    area_hectares = geom_transformed.area / 10000

    # For now, the percentage is a fixed value
    percentage = 100.0

    # Include properties for reference
    properties = feature.properties

    return area_hectares, percentage, properties

def get_vertice_and_total_area(geometry):
    """
    Extracts vertices in UTM and calculates the total area in hectares of a GeoJSON geometry.
    """
    geom = geom_shape(geometry.model_dump())

    # Get the centroid of the geometry to determine the UTM zone
    centroid = geom.centroid
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree=centroid.x,
            south_lat_degree=centroid.y,
            east_lon_degree=centroid.x,
            north_lat_degree=centroid.y,
        ),
    )
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)

    # Define the transformation from WGS84 to UTM
    transformer = Transformer.from_crs(CRS("EPSG:4326"), utm_crs, always_xy=True)

    # Transform the geometry to UTM
    geom_transformed = transform(transformer.transform, geom)

    # Calculate the area in square meters and convert to hectares
    area_hectares = geom_transformed.area / 10000

    # Extract vertices in UTM
    vertices_utm = []
    if geom_transformed.geom_type == "Polygon":
        for x, y in list(geom_transformed.exterior.coords):
            vertices_utm.append([round(x, 4), round(y, 4)])
    elif geom_transformed.geom_type == "MultiPolygon":
        for poly in geom_transformed.geoms:
            for x, y in list(poly.exterior.coords):
                vertices_utm.append([round(x, 4), round(y, 4)])

    return vertices_utm, area_hectares
