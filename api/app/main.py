"""MS5 - API Rest Consultas Analiticas.

El unico microservicio del proyecto sin base de datos propia relacional:
ejecuta consultas Athena (sobre el catalogo Glue poblado por ingesta/) y
las expone como JSON. Documentacion interactiva en /docs (swagger-ui).
"""
import logging
import os

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.athena_client import AthenaQueryError, run_query
from app.queries import QUERIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ms5-api")

app = FastAPI(
    title="MS5 - API Rest Consultas Analiticas",
    description=(
        "Ejecuta 4 consultas Athena sobre 2 vistas (vista_viajes_completos y "
        "vista_conexiones_completas) construidas con JOIN sobre los datos "
        "ingeridos de MS1/MS2/MS3."
    ),
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Estado del servicio")
def health():
    return {"status": "ok"}


def _run(name):
    try:
        return run_query(QUERIES[name])
    except AthenaQueryError as exc:
        logger.exception("Fallo la consulta Athena '%s'", name)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Error de AWS/boto3 en la consulta '%s'", name)
        raise HTTPException(status_code=502, detail=f"Error de AWS: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - ultimo recurso, nunca 500 opaco
        logger.exception("Error inesperado en la consulta '%s'", name)
        raise HTTPException(status_code=500, detail=f"Error inesperado: {exc}") from exc


@app.get("/analitica/demanda-por-ruta", summary="Consulta 1: demanda por ruta")
def demanda_por_ruta():
    return _run("demanda_por_ruta")


@app.get("/analitica/demanda-por-paradero", summary="Consulta 2: demanda por paradero")
def demanda_por_paradero():
    return _run("demanda_por_paradero")


@app.get("/analitica/demanda-por-hora", summary="Consulta 3: demanda por hora del dia, por ruta")
def demanda_por_hora():
    return _run("demanda_por_hora")


@app.get("/analitica/trasbordos-por-ruta-destino", summary="Consulta 4: rutas que más reciben trasbordos")
def trasbordos_por_ruta_destino():
    return _run("trasbordos_por_ruta_destino")