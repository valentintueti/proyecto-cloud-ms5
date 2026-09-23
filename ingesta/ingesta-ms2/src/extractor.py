from pymongo import MongoClient
from config import settings


def _conectar():
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=10000)
    return client, client[settings.DB_NAME]


def extraer_rutas() -> list[dict]:
    client, db = _conectar()
    docs = list(db.rutas.find({}))
    client.close()
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


def extraer_paraderos() -> list[dict]:
    client, db = _conectar()
    docs = list(db.paraderos.find({}))
    client.close()
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


def extraer_servicios() -> list[dict]:
    client, db = _conectar()
    docs = list(db.servicios.find({}))
    client.close()
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs