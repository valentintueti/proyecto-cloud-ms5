
DB = "transporte"

QUERIES = {
    "demanda_por_ruta": f"""
        SELECT ruta_nombre, ruta_sentido, COUNT(*) AS total_viajes
        FROM {DB}.vista_viajes_completos
        GROUP BY ruta_nombre, ruta_sentido
        ORDER BY total_viajes DESC
    """,
    "demanda_por_paradero": f"""
        SELECT paradero_origen, COUNT(*) AS total_viajes
        FROM {DB}.vista_viajes_completos
        GROUP BY paradero_origen
        ORDER BY total_viajes DESC
    """,
    "demanda_por_hora": f"""
        SELECT ruta_nombre, hour(fecha_hora) AS hora_del_dia, COUNT(*) AS total_viajes
        FROM {DB}.vista_viajes_completos
        GROUP BY ruta_nombre, hour(fecha_hora)
        ORDER BY ruta_nombre, hora_del_dia
    """,
    "trasbordos_por_ruta_destino": f"""
        SELECT ruta_destino, COUNT(*) AS total_conexiones
        FROM {DB}.vista_conexiones_completas
        GROUP BY ruta_destino
        ORDER BY total_conexiones DESC
    """,
}