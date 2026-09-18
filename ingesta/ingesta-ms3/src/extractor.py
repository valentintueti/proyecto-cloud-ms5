from contextlib import closing
from common import ConfigurationError, database_config, write_csv


def find_table(cursor, name):
    cursor.execute("SELECT TABLE_NAME FROM information_schema.tables "
                   "WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) = %s "
                   "AND TABLE_TYPE = 'BASE TABLE'", (name,))
    matches = cursor.fetchall()
    if len(matches) > 1:
        raise ConfigurationError("Hay varias tablas con el mismo nombre ignorando mayúsculas.")
    return matches[0][0] if matches else None


def extraer_viajes_y_pagos(directory, warnings):
    import pymysql
    config = database_config()
    with closing(pymysql.connect(**config, charset="utf8mb4", connect_timeout=10,
                                 read_timeout=60, write_timeout=60, autocommit=False)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
            viaje = find_table(cursor, "viaje")
            pago = find_table(cursor, "pago")
        if not viaje:
            raise ConfigurationError("No existe la tabla Viaje en la BD configurada.")
        tables = [(viaje, "viajes")]
        if pago:
            tables.append((pago, "pagos"))
        else:
            warnings.append("Pago pendiente: la tabla Pago no existe; se continúa solo con Viaje.")
        exports = []
        for table, dataset in tables:
            with connection.cursor(pymysql.cursors.SSCursor) as cursor:
                # Table name comes exclusively from information_schema, not user input.
                escaped = table.replace("`", "``")
                cursor.execute(f"SELECT * FROM `{escaped}`")
                columns = [item[0] for item in cursor.description]
                exports.append(write_csv(directory, dataset, columns, cursor))
        connection.rollback()
        return exports
