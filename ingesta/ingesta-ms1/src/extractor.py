from contextlib import closing
from common import database_config, write_csv


def extraer_pasajeros_y_tarjetas(directory, warnings):
    import psycopg2
    config = database_config()
    # Both tables come from the same read-only snapshot. No JOIN drops passengers
    # without cards or duplicates passenger records for people with multiple cards.
    with closing(psycopg2.connect(**config, connect_timeout=10, client_encoding="UTF8")) as connection:
        connection.set_session(readonly=True, isolation_level="REPEATABLE READ")
        exports = []
        for table, dataset in (("pasajero", "pasajeros"), ("tarjeta", "tarjetas")):
            with connection.cursor(name=f"export_{table}") as cursor:
                cursor.itersize = 2000
                cursor.execute(f'SELECT * FROM "{table}"')
                first = cursor.fetchmany(2000)
                columns = [item.name for item in cursor.description]

                def rows():
                    yield from first
                    while True:
                        batch = cursor.fetchmany(2000)
                        if not batch:
                            break
                        yield from batch

                exports.append(write_csv(directory, dataset, columns, rows()))
        connection.rollback()
        return exports
