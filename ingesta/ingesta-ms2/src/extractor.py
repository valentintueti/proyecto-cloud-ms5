from pymongo import MongoClient
from config import settings


def _conectar():
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=10000)
    return client, client[settings.DB_NAME]


def _renombrar_id(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


def extraer_rutas() -> list[dict]:
    client, db = _conectar()
    docs = [_renombrar_id(d) for d in db.rutas.find({})]
    client.close()
    return docs


def extraer_paraderos() -> list[dict]:
    client, db = _conectar()
    docs = [_renombrar_id(d) for d in db.paraderos.find({})]
    client.close()
    return docs


def extraer_servicios() -> list[dict]:
    client, db = _conectar()
    docs = [_renombrar_id(d) for d in db.servicios.find({})]
    client.close()
    return docs