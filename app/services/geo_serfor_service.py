"""
Servicio para consultar la zonificación forestal desde GeoSERFOR.

Este módulo se encarga de:
1. Consultar el servicio ArcGIS REST de GeoSERFOR
2. Realizar intersección espacial con la geometría del Bosque Local
3. Calcular áreas y porcentajes de cada zona
4. Guardar los resultados en la base de datos
"""

import requests
from shapely.geometry import shape as geom_shape, mapping
from shapely.ops import transform, unary_union
from pyproj import CRS, Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from typing import List, Dict, Any, Optional, Tuple
import json

# URL base del servicio ArcGIS REST de GeoSERFOR
# MapServer: Modalidad_Acceso contiene múltiples capas forestales
GEOSERFOR_BASE_URL = "https://geo.serfor.gob.pe/geoservicios/rest/services/Servicios_OGC/Modalidad_Acceso/MapServer"

# Capas disponibles en este MapServer:
#   0 - Permisos
#   1 - Cesiones_en_Uso
#   2 - Autorizaciones_de_PFDM_en_AVNB
#   3 - Autorizacion_de_cambio_de_uso_actual_de_las_tierras_a_fines_agropecuarios
#   4 - Bosques_Locales  ← Esta contiene información de Bosques Locales
#   5 - Unidad_de_Aprovechamiento
#   6 - Concesiones_Forestales
#
# NOTA: No hay una capa específica de "Zonificación Forestal" en este servicio.
# Usamos la capa 4 (Bosques_Locales) como referencia para la zonificación.

ZONIFICACION_LAYER_ID = 4  # Capa de Bosques_Locales


def consultar_geoserfor(
    geometry_wgs84: Dict[str, Any],
    layer_id: int = ZONIFICACION_LAYER_ID,
    out_fields: str = "*"
) -> Optional[Dict[str, Any]]:
    """
    Consulta el servicio ArcGIS REST de GeoSERFOR para obtener features que intersecten
    con la geometría proporcionada.
    
    Args:
        geometry_wgs84: Geometría en formato GeoJSON (EPSG:4326)
        layer_id: ID de la capa en el MapServer
        out_fields: Campos a retornar (default: todos)
    
    Returns:
        Diccionario con la respuesta de GeoSERFOR o None si hay error
    """
    # Convertir geometría GeoJSON a formato Esri
    esri_geometry = geojson_to_esri_geometry(geometry_wgs84)
    
    if not esri_geometry:
        print("No se pudo convertir la geometría a formato Esri")
        return None
    
    # Endpoint query del layer
    url = f"{GEOSERFOR_BASE_URL}/{layer_id}/query"
    
    # Parámetros de la consulta
    params = {
        "geometry": json.dumps(esri_geometry),
        "geometryType": "esriGeometryPolygon",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "outSR": "4326",  # Retornar en WGS84
        "f": "json",
        "returnGeometry": "true"
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        
        # Debug: mostrar status
        print(f"   Status: {response.status_code}")
        
        response.raise_for_status()
        result = response.json()
        
        # Verificar si hay error en la respuesta
        if "error" in result:
            error = result["error"]
            print(f"   Detalles: {error.get('details', [])}")
            return None
        
        features = result.get("features", [])
        print(f"Features encontrados: {len(features)}")
        
        return result
        
    except requests.exceptions.Timeout:
        print("Timeout al consultar GeoSERFOR (60s)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f" Error HTTP: {e}")
        print(f"   Response: {e.response.text[:200] if e.response else 'N/A'}")
        return None
    except requests.exceptions.RequestException as e:
        print(f" Error de conexión con GeoSERFOR: {e}")
        return None
    except Exception as e:
        print(f" Error procesando respuesta de GeoSERFOR: {e}")
        return None


def geojson_to_esri_geometry(geojson_geom: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convierte una geometría GeoJSON a formato Esri.

    Args:
        geojson_geom: Diccionario con geometría GeoJSON

    Returns:
        Diccionario con geometría en formato Esri o None si hay error
    """
    try:
        geom_type = geojson_geom.get("type", "").lower()
        coordinates = geojson_geom.get("coordinates", [])
        
        # Debug: mostrar qué geometría se está recibiendo
        print(f"Convirtiendo geometría: type={geom_type}, coords={len(coordinates)} elementos")

        if geom_type == "polygon":
            # Esri Polygon: {"rings": [[[x,y], [x,y], ...]]}
            # GeoJSON Polygon: [ring] donde ring = [[x,y], [x,y], ...]
            rings = []
            for ring in coordinates:
                esri_ring = [[round(coord[0], 6), round(coord[1], 6)] for coord in ring]
                # Asegurar que el anillo esté cerrado
                if len(esri_ring) > 1 and esri_ring[0] != esri_ring[-1]:
                    esri_ring.append(esri_ring[0])
                rings.append(esri_ring)

            return {
                "rings": rings,
                "spatialReference": {"wkid": 4326}
            }

        elif geom_type == "multipolygon":
            # GeoJSON MultiPolygon: [polygon] donde polygon = [ring]
            rings = []
            for polygon in coordinates:
                for ring in polygon:
                    esri_ring = [[round(coord[0], 6), round(coord[1], 6)] for coord in ring]
                    if len(esri_ring) > 1 and esri_ring[0] != esri_ring[-1]:
                        esri_ring.append(esri_ring[0])
                    rings.append(esri_ring)

            return {
                "rings": rings,
                "spatialReference": {"wkid": 4326}
            }

        elif geom_type == "point":
            return {
                "x": coordinates[0],
                "y": coordinates[1],
                "spatialReference": {"wkid": 4326}
            }

        elif geom_type == "linestring":
            # Esri Polyline: {"paths": [[[x,y], [x,y], ...]]}
            paths = [[[round(coord[0], 6), round(coord[1], 6)] for coord in coordinates]]
            return {
                "paths": paths,
                "spatialReference": {"wkid": 4326}
            }

        elif geom_type == "multilinestring":
            paths = []
            for line in coordinates:
                esri_path = [[round(coord[0], 6), round(coord[1], 6)] for coord in line]
                paths.append(esri_path)
            return {
                "paths": paths,
                "spatialReference": {"wkid": 4326}
            }

        elif geom_type == "multipoint":
            # GeoJSON MultiPoint: [[x,y], [x,y], ...]
            # Esri MultiPoint: {"points": [[x,y], [x,y], ...]}
            points = [[round(coord[0], 6), round(coord[1], 6)] for coord in coordinates]
            return {
                "points": points,
                "spatialReference": {"wkid": 4326}
            }

        else:
            print(f"Tipo de geometría no soportado: {geom_type}")
            print(f"   GeoJSON completo: {geojson_geom}")
            return None

    except Exception as e:
        print(f" Error convirtiendo GeoJSON a Esri: {e}")
        import traceback
        traceback.print_exc()
        return None


def esri_feature_to_shapely(esri_feature: Dict[str, Any]) -> Optional[Any]:
    """
    Convierte un feature de Esri a geometría Shapely.

    Args:
        esri_feature: Feature de respuesta ArcGIS

    Returns:
        Geometría Shapely o None
    """
    try:
        geometry = esri_feature.get("geometry")
        if not geometry:
            return None

        # Convertir de formato Esri a GeoJSON
        if "rings" in geometry:
            # Esri Polygon: {"rings": [[[x,y], [x,y], ...]]}
            rings = geometry["rings"]
            
            # Verificar estructura de rings
            # Si rings[0][0] es un número, es un Polygon simple (los puntos están directos)
            # Si rings[0][0] es una lista, es MultiPolygon (anidados)
            if len(rings) > 0 and len(rings[0]) > 0:
                first_elem = rings[0][0]
                
                if isinstance(first_elem, (int, float)):
                    # Polygon simple: rings = [[x,y], [x,y], ...]
                    # Esto no debería pasar según spec de Esri, pero lo manejamos
                    coords = [[rings]]  # Forzar estructura MultiPolygon
                    geojson_geom = {"type": "Polygon", "coordinates": coords}
                elif isinstance(first_elem, list):
                    # MultiPolygon o Polygon con holes
                    # rings = [[[x,y], ...], [[x,y], ...]]
                    # Primer anillo es exterior, los demás son holes
                    if len(rings) == 1:
                        # Polygon simple con un solo anillo
                        coords = [[ [p[0], p[1]] for p in rings[0] ]]
                        geojson_geom = {"type": "Polygon", "coordinates": coords}
                    else:
                        # Múltiples anillos (posibles holes)
                        # Asumimos que todos son polígonos separados para simplificar
                        coords = []
                        for ring in rings:
                            poly_coords = [[p[0], p[1]] for p in ring]
                            coords.append([poly_coords])
                        if len(coords) == 1:
                            geojson_geom = {"type": "Polygon", "coordinates": coords[0]}
                        else:
                            geojson_geom = {"type": "MultiPolygon", "coordinates": coords}
                else:
                    return None
            else:
                return None

        elif "paths" in geometry:
            # Esri Polyline: {"paths": [[[x,y], [x,y], ...]]}
            paths = geometry["paths"]
            if len(paths) == 1:
                coords = [[p[0], p[1]] for p in paths[0]]
                geojson_geom = {"type": "LineString", "coordinates": coords}
            else:
                coords = [[[p[0], p[1]] for p in path] for path in paths]
                geojson_geom = {"type": "MultiLineString", "coordinates": coords}

        elif "x" in geometry and "y" in geometry:
            # Esri Point
            geojson_geom = {
                "type": "Point",
                "coordinates": [geometry["x"], geometry["y"]]
            }

        else:
            return None

        return geom_shape(geojson_geom)

    except Exception as e:
        print(f"Error convirtiendo feature Esri a Shapely: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_area_utm(geometry: Any) -> Tuple[float, str]:
    """
    Calcula el área de una geometría en hectáreas usando la zona UTM apropiada.
    
    Args:
        geometry: Geometría Shapely en WGS84
    
    Returns:
        Tupla con (área en hectáreas, zona UTM)
    """
    try:
        centroid = geometry.centroid
        
        # Obtener CRS UTM apropiado para la ubicación
        utm_crs_list = query_utm_crs_info(
            datum_name="WGS 84",
            area_of_interest=AreaOfInterest(
                west_lon_degree=centroid.x,
                south_lat_degree=centroid.y,
                east_lon_degree=centroid.x,
                north_lat_degree=centroid.y,
            ),
        )
        
        if not utm_crs_list:
            # Default a UTM 18S (Perú)
            utm_crs = CRS.from_epsg(32718)
            utm_zone = "18S"
        else:
            utm_crs = CRS.from_epsg(utm_crs_list[0].code)
            utm_zone = str(utm_crs_list[0].code)
        
        # Transformar a UTM
        transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
        geom_utm = transform(transformer.transform, geometry)
        
        # Calcular área en hectáreas
        area_ha = geom_utm.area / 10000.0
        
        return area_ha, utm_zone
        
    except Exception as e:
        print(f"Error calculando área UTM: {e}")
        return 0.0, "Desconocida"


def procesar_features_geoserfor(
    features: List[Dict[str, Any]],
    bosque_local_geometry: Any
) -> List[Dict[str, Any]]:
    """
    Procesa los features obtenidos de GeoSERFOR:
    - Realiza intersección con la geometría del Bosque Local
    - Calcula área de cada zona
    - Calcula porcentaje respecto al área total
    
    Args:
        features: Lista de features de GeoSERFOR
        bosque_local_geometry: Geometría Shapely del Bosque Local
    
    Returns:
        Lista de diccionarios con zonificación procesada
    """
    # Calcular área total del Bosque Local
    area_total_ha, _ = calculate_area_utm(bosque_local_geometry)
    
    resultados = []
    
    for feature in features:
        try:
            # Convertir geometría Esri a Shapely
            geom = esri_feature_to_shapely(feature)
            if not geom:
                continue
            
            # Realizar intersección con el Bosque Local
            try:
                interseccion = geom.intersection(bosque_local_geometry)
                
                # Si no hay intersección o es vacía, saltar
                if interseccion.is_empty or interseccion.area == 0:
                    continue
                    
            except Exception as e:
                # Si falla la intersección, usar la geometría completa
                print(f"Intersección falló, usando geometría completa: {e}")
                interseccion = geom
            
            # Calcular área de la zona intersectada
            area_ha, utm_zone = calculate_area_utm(interseccion)
            
            # Calcular porcentaje
            porcentaje = (area_ha / area_total_ha * 100) if area_total_ha > 0 else 0.0
            
            # Extraer atributos del feature
            attributes = feature.get("attributes", {})
            
            # Buscar campo de denominación (puede variar según la capa)
            # Para la capa Bosques_Locales (ID 4), los campos relevantes son:
            # - NOMBOS: Nombre del bosque local
            # - TIPBLO: Tipo de bosque
            # - NOMTIT: Nombre del titular
            denominacion = (
                attributes.get("NOMBOS") or
                attributes.get("DENOMINACION") or
                attributes.get("DENOMINAC") or
                attributes.get("NOMBRE") or
                attributes.get("ZONA") or
                attributes.get("TIPO") or
                attributes.get("descripcion") or
                "Sin denominación"
            )
            
            resultados.append({
                "denominacion": denominacion,
                "superficie_ha": round(area_ha),
                "porcentaje": round(porcentaje),
                "utm_zone": utm_zone,
                "geometria": mapping(interseccion) if interseccion else None,
                "atributos_originales": attributes
            })
            
        except Exception as e:
            print(f" Error procesando feature: {e}")
            continue
    
    return resultados


def obtener_zonificacion_geoserfor(
    bosque_local_geometry: Dict[str, Any],
    layer_id: int = ZONIFICACION_LAYER_ID
) -> Dict[str, Any]:
    """
    Función principal para obtener la zonificación desde GeoSERFOR.
    
    Args:
        bosque_local_geometry: Geometría del Bosque Local en GeoJSON
        layer_id: ID de la capa de zonificación en GeoSERFOR
    
    Returns:
        Diccionario con resultados de la zonificación
    """
    # 1. Consultar GeoSERFOR
    response = consultar_geoserfor(
        geometry_wgs84=bosque_local_geometry,
        layer_id=layer_id
    )
    
    if not response:
        return {
            "success": False,
            "error": "No se pudo conectar con GeoSERFOR. Verificar que el servicio esté disponible y la geometría sea válida.",
            "zonificaciones": []
        }
    
    features = response.get("features", [])
    
    if not features:
        return {
            "success": True,
            "message": "No se encontró información de Zonificación u Ordenamiento Forestal para el área.",
            "zonificaciones": []
        }
    
    # 2. Convertir geometría del Bosque Local a Shapely
    try:
        bl_geometry = geom_shape(bosque_local_geometry)
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al procesar geometría del Bosque Local: {e}",
            "zonificaciones": []
        }
    
    # 3. Procesar features
    zonificaciones = procesar_features_geoserfor(
        features=features,
        bosque_local_geometry=bl_geometry
    )
    
    if not zonificaciones:
        return {
            "success": True,
            "message": "No se encontró información de Zonificación u Ordenamiento Forestal para el área.",
            "zonificaciones": []
        }
    
    # 4. Calcular totales para validación
    total_ha = sum(z["superficie_ha"] for z in zonificaciones)
    total_porcentaje = sum(z["porcentaje"] for z in zonificaciones)
    
    return {
        "success": True,
        "zonificaciones": zonificaciones,
        "total_superficie_ha": round(total_ha, 4),
        "total_porcentaje": round(total_porcentaje, 2),
        "features_originales": len(features),
        "features_procesados": len(zonificaciones)
    }


def guardar_zonificacion_en_bd(
    engine,
    id_solicitud: int,
    zonificaciones: List[Dict[str, Any]],
    fuente_datos: str = "GEOSERFOR",
    reemplazar: bool = False
) -> bool:
    """
    Guarda o actualiza la zonificación en la base de datos usando stored procedure.
    
    Args:
        engine: Motor de SQLAlchemy
        id_solicitud: ID de la solicitud
        zonificaciones: Lista de zonificaciones procesadas
        fuente_datos: Fuente de los datos (default: GEOSERFOR)
        reemplazar: Si True, elimina registros anteriores antes de insertar
    
    Returns:
        True si se guardó correctamente, False en caso de error
    """
    from sqlalchemy import text
    
    if not zonificaciones:
        return False
    
    try:
        with engine.connect() as conn:
            # Si se debe reemplazar, eliminar registros anteriores
            if reemplazar:
                conn.execute(
                    text("""
                        EXEC BosqueLocal.pa_BosqueLocalZonificacion_Eliminar
                            @IdSolicitud = :id_solicitud,
                            @IdUsuario = 1;
                    """),
                    {"id_solicitud": id_solicitud}
                )
                conn.commit()
            
            # Insertar cada zonificación usando SP
            for zonif in zonificaciones:
                conn.execute(
                    text("""
                        EXEC BosqueLocal.pa_BosqueLocalZonificacion_Registrar
                            @IdSolicitud = :id_solicitud,
                            @Denominacion = :denominacion,
                            @SuperficieHa = :superficie_ha,
                            @Porcentaje = :porcentaje,
                            @FuenteDatos = :fuente_datos,
                            @IdUsuarioRegistro = 1;
                    """),
                    {
                        "id_solicitud": id_solicitud,
                        "denominacion": zonif["denominacion"],
                        "superficie_ha": zonif["superficie_ha"],
                        "porcentaje": zonif["porcentaje"],
                        "fuente_datos": fuente_datos
                    }
                )
            
            conn.commit()
            return True
            
    except Exception as e:
        print(f"Error guardando zonificación en BD: {e}")
        return False


def verificar_zonificacion_existente(
    engine,
    id_solicitud: int
) -> bool:
    """
    Verifica si ya existen registros de zonificación para una solicitud usando stored procedure.
    
    Args:
        engine: Motor de SQLAlchemy
        id_solicitud: ID de la solicitud
    
    Returns:
        True si existen registros, False en caso contrario
    """
    from sqlalchemy import text
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    EXEC BosqueLocal.pa_BosqueLocalZonificacion_Verificar
                        @IdSolicitud = :id_solicitud;
                """),
                {"id_solicitud": id_solicitud}
            )
            row = result.fetchone()
            return row.Existe == 1 if row else False
            
    except Exception as e:
        print(f"Error verificando zonificación existente: {e}")
        return False


def obtener_zonificacion_guardada(
    engine,
    id_solicitud: int
) -> List[Dict[str, Any]]:
    """
    Obtiene la zonificación guardada para una solicitud usando stored procedure.
    
    Args:
        engine: Motor de SQLAlchemy
        id_solicitud: ID de la solicitud
    
    Returns:
        Lista de zonificaciones guardadas
    """
    from sqlalchemy import text
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    EXEC BosqueLocal.pa_BosqueLocalZonificacion_Listar
                        @IdSolicitud = :id_solicitud;
                """),
                {"id_solicitud": id_solicitud}
            )
            
            zonificaciones = []
            for row in result:
                zonificaciones.append({
                    "id_zonificacion": row.NU_ID_ZONIFICACION,
                    "id_solicitud": row.NU_ID_SOLICITUD,
                    "denominacion": row.TX_DENOMINACION,
                    "superficie_ha": float(row.NU_SUPERFICIE_HA),
                    "porcentaje": float(row.NU_PORCENTAJE),
                    "fuente_datos": row.TX_FUENTE_DATOS
                })
            
            return zonificaciones
            
    except Exception as e:
        print(f" Error obteniendo zonificación guardada: {e}")
        return []
