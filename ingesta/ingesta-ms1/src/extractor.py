import psycopg2
import pandas as pd
from config import settings


def _conectar():
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )


def extraer_pasajeros() -> pd.DataFrame:
    conn = _conectar()
    df = pd.read_sql("SELECT id, nombre, fecha_nacimiento, sexo, distrito FROM pasajero", conn)
    conn.close()
    return df


def extraer_tarjetas() -> pd.DataFrame:
    conn = _conectar()
    df = pd.read_sql(
        "SELECT id, pasajero_id, fecha_emision, fecha_vencimiento, tipo, saldo FROM tarjeta",
        conn
    )
    conn.close()
    return df