"""MS5 - API Rest Consultas Analiticas.

El unico microservicio del proyecto sin base de datos propia relacional:
ejecuta consultas Athena (sobre el catalogo Glue poblado por ingesta/) y
las expone como JSON. Documentacion interactiva en /docs (swagger-ui).
"""
import logging

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
        "Ejecuta consultas Athena sobre los datos ingeridos de MS1/MS2/MS3 "
        "(via el catalogo Glue en el bucket S3 de la ingesta) y las expone "
        "como JSON para el frontend."
    ),
    version="1.0.0",
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
        # Credenciales expiradas/invalidas, bucket sin permisos, etc. Se
        # expone el mensaje real (no es produccion) para poder depurar sin
        # tener que ir a buscar los logs del contenedor cada vez.
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


@app.get("/analitica/evolucion-mensual", summary="Consulta 4: evolucion mensual de la demanda")
def evolucion_mensual():
    return _run("evolucion_mensual")


@app.get("/analitica/paraderos-por-perfil", summary="Consulta 5: paraderos mas visitados por edad/distrito")
def paraderos_por_perfil():
    return _run("paraderos_por_perfil")


@app.get("/analitica/concentracion-pasajeros", summary="Consulta 6: concentracion de pasajeros (Pareto)")
def concentracion_pasajeros():
    return _run("concentracion_pasajeros")


@app.get("/analitica/saldo-flotante", summary="Consulta 7: saldo flotante total en tarjetas")
def saldo_flotante():
    return _run("saldo_flotante")


@app.get("/analitica/viajes-fuera-horario", summary="Consulta 8: viajes fuera del horario declarado")
def viajes_fuera_horario():
    return _run("viajes_fuera_horario")


@app.get("/analitica/ingresos-por-ruta", summary="Vista: ingresos por ruta y mes")
def ingresos_por_ruta():
    return _run("ingresos_por_ruta")
