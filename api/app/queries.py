"""SQL exacto validado en vivo contra Athena real (ver
avance_consultas/ms5_consultas_athena_vistas.md). No se reescribe nada aqui:
cada entrada es copia textual de una consulta/vista ya probada, para que la
API nunca diverja silenciosamente del SQL documentado."""

DB = "transporte_metropolitano"

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
    "evolucion_mensual": f"""
        SELECT date_trunc('month', fecha_hora) AS mes, ruta_nombre, COUNT(*) AS total_viajes
        FROM {DB}.vista_viajes_completos
        GROUP BY date_trunc('month', fecha_hora), ruta_nombre
        ORDER BY mes, ruta_nombre
    """,
    "paraderos_por_perfil": f"""
        SELECT
            paradero_origen,
            distrito,
            CASE
              WHEN date_diff('year', fecha_nacimiento, CURRENT_DATE) < 18 THEN 'menor_18'
              WHEN date_diff('year', fecha_nacimiento, CURRENT_DATE) BETWEEN 18 AND 30 THEN '18_30'
              WHEN date_diff('year', fecha_nacimiento, CURRENT_DATE) BETWEEN 31 AND 60 THEN '31_60'
              ELSE 'mayor_60'
            END AS rango_edad,
            COUNT(*) AS total_visitas
        FROM {DB}.vista_viajes_completos
        GROUP BY paradero_origen, distrito,
          CASE
            WHEN date_diff('year', fecha_nacimiento, CURRENT_DATE) < 18 THEN 'menor_18'
            WHEN date_diff('year', fecha_nacimiento, CURRENT_DATE) BETWEEN 18 AND 30 THEN '18_30'
            WHEN date_diff('year', fecha_nacimiento, CURRENT_DATE) BETWEEN 31 AND 60 THEN '31_60'
            ELSE 'mayor_60'
          END
        ORDER BY total_visitas DESC
    """,
    "concentracion_pasajeros": f"""
        WITH viajes_por_pasajero AS (
            SELECT v.pasajero_id, p.distrito, COUNT(*) AS total_viajes
            FROM {DB}.viajes v
            JOIN {DB}.pasajeros p ON v.pasajero_id = p.id
            GROUP BY v.pasajero_id, p.distrito
        ),
        ranking AS (
            SELECT pasajero_id, distrito, total_viajes,
                SUM(total_viajes) OVER (ORDER BY total_viajes DESC) AS viajes_acumulados,
                SUM(total_viajes) OVER () AS viajes_totales,
                ROW_NUMBER() OVER (ORDER BY total_viajes DESC) AS posicion,
                COUNT(*) OVER () AS total_pasajeros
            FROM viajes_por_pasajero
        )
        SELECT pasajero_id, distrito, total_viajes,
            ROUND(100.0 * posicion / total_pasajeros, 1) AS pct_pasajeros_acumulado,
            ROUND(100.0 * viajes_acumulados / viajes_totales, 1) AS pct_viajes_acumulado
        FROM ranking
        ORDER BY posicion
    """,
    "saldo_flotante": f"""
        SELECT
            t.tipo,
            p.distrito,
            COUNT(*) AS total_tarjetas,
            SUM(CAST(t.saldo AS DOUBLE)) AS saldo_flotante_total
        FROM {DB}.tarjetas t
        JOIN {DB}.pasajeros p ON t.pasajero_id = p.id
        GROUP BY t.tipo, p.distrito
        ORDER BY saldo_flotante_total DESC
    """,
    "viajes_fuera_horario": f"""
        SELECT v.id AS viaje_id, v.fecha_hora, s.ruta_nombre, s.hora_inicio, s.hora_fin
        FROM {DB}.viajes v
        JOIN {DB}.servicios s ON v.servicio_id = s.id
        WHERE (
            hour(date_parse(v.fecha_hora, '%Y-%m-%dT%H:%i:%s')) * 60
            + minute(date_parse(v.fecha_hora, '%Y-%m-%dT%H:%i:%s'))
          ) NOT BETWEEN
          (
            CAST(split_part(s.hora_inicio, ':', 1) AS INTEGER) * 60
            + CAST(split_part(s.hora_inicio, ':', 2) AS INTEGER)
          )
          AND
          (
            CAST(split_part(s.hora_fin, ':', 1) AS INTEGER) * 60
            + CAST(split_part(s.hora_fin, ':', 2) AS INTEGER)
          )
    """,
    "trasbordos_por_ruta_destino": f"""
        SELECT ruta_destino, COUNT(*) AS total_conexiones
        FROM {DB}.vista_conexiones_completas
        GROUP BY ruta_destino
        ORDER BY total_conexiones DESC
    """,
}
