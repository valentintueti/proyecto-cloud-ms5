import pymysql
from config import settings


def _conectar():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )


def extraer_viajes():
    conn = _conectar()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM viaje")
        rows = cursor.fetchall()
    conn.close()
    return rows


def extraer_conexiones():
    conn = _conectar()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM conexion")
        rows = cursor.fetchall()
    conn.close()
    return rows