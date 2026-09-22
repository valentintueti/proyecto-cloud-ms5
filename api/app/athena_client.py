"""Cliente delgado sobre boto3 para ejecutar consultas Athena y devolver
filas como diccionarios JSON-serializables.

No usa PyAthena ni ningun ORM a proposito: son dos llamadas de boto3
(start_query_execution + poll de get_query_execution) y paginacion manual
de get_query_results. Mantenerlo simple facilita depurar errores de Athena
sin una capa extra en medio.
"""
import os
import time

import boto3


class AthenaQueryError(Exception):
    """Consulta Athena en FAILED/CANCELLED, timeout, o configuracion faltante."""


def _required(name):
    value = os.environ.get(name)
    if not value:
        raise AthenaQueryError(f"Falta la variable de entorno {name}.")
    return value


def _coerce(value):
    """Athena devuelve todo como texto (VarCharValue); esto intenta recuperar
    int/float para que el JSON de salida no obligue al frontend a parsear
    numeros el mismo desde string."""
    if value is None:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def run_query(sql, poll_seconds=1, timeout_seconds=60):
    region = _required("AWS_REGION")
    database = _required("ATHENA_DATABASE")
    output_location = _required("ATHENA_OUTPUT_LOCATION")

    client = boto3.client("athena", region_name=region)
    exec_id = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": output_location},
    )["QueryExecutionId"]

    elapsed = 0
    state = "QUEUED"
    status = {}
    while elapsed <= timeout_seconds:
        status = client.get_query_execution(QueryExecutionId=exec_id)["QueryExecution"]["Status"]
        state = status["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(poll_seconds)
        elapsed += poll_seconds

    if state != "SUCCEEDED":
        reason = status.get("StateChangeReason", "sin detalle (o se agoto el tiempo de espera)")
        raise AthenaQueryError(f"Consulta Athena en estado {state}: {reason}")

    columns = None
    rows = []
    next_token = None
    first_page = True
    while True:
        kwargs = {"QueryExecutionId": exec_id, "MaxResults": 1000}
        if next_token:
            kwargs["NextToken"] = next_token
        page = client.get_query_results(**kwargs)
        result_rows = page["ResultSet"]["Rows"]
        if columns is None:
            columns = [c["Label"] for c in page["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
        # Athena repite la fila de encabezado solo en la primera pagina.
        data_rows = result_rows[1:] if first_page else result_rows
        for row in data_rows:
            values = [cell.get("VarCharValue") for cell in row["Data"]]
            rows.append({col: _coerce(val) for col, val in zip(columns, values)})
        first_page = False
        next_token = page.get("NextToken")
        if not next_token:
            break
    return rows
