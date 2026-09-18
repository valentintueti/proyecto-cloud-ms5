"""CSV exports, Learner Lab preflight and execution reports shared by three jobs."""
import argparse
import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4


class ConfigurationError(RuntimeError):
    pass


def required(name):
    value = os.environ.get(name, "")
    if not value.strip():
        raise ConfigurationError(f"Falta configurar {name}.")
    return value


def database_config():
    return {
        "host": required("DB_HOST"),
        "port": int(required("DB_PORT")),
        "database": required("DB_NAME"),
        "user": required("DB_USER"),
        "password": required("DB_PASSWORD"),
    }


@dataclass
class Export:
    name: str
    path: Path
    rows: int


def csv_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def write_csv(directory, name, columns, rows):
    """Stream rows; preserve headers even for empty tables and avoid float casts."""
    path = Path(directory) / f"{name}.csv"
    count = 0
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([csv_value(value) for value in row])
            count += 1
    return Export(name, path, count)


def aws_preflight():
    """Read-only: token + STS account + S3 bucket owner; never creates a bucket."""
    bucket = required("S3_BUCKET")
    account = required("AWS_EXPECTED_ACCOUNT_ID")
    if not re.fullmatch(r"\d{12}", account):
        raise ConfigurationError("AWS_EXPECTED_ACCOUNT_ID debe tener 12 dígitos.")
    region = required("AWS_REGION")
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError

    session = boto3.Session(region_name=region)
    credentials = session.get_credentials()
    if credentials is None:
        raise ConfigurationError("Boto3 no encontró credenciales AWS.")
    frozen = credentials.get_frozen_credentials()
    if not all((frozen.access_key, frozen.secret_key, frozen.token)):
        raise ConfigurationError("Learner Lab requiere access key, secret y session token.")
    config = Config(connect_timeout=10, read_timeout=30,
                    retries={"max_attempts": 2, "mode": "standard"})
    identity = session.client("sts", config=config).get_caller_identity()
    if identity["Account"] != account:
        raise ConfigurationError("La cuenta AWS activa no coincide con el Learner Lab personal configurado.")
    s3 = session.client("s3", config=config)
    try:
        s3.head_bucket(Bucket=bucket, ExpectedBucketOwner=account)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in ("404", "NoSuchBucket", "NotFound"):
            raise ConfigurationError("El bucket no fue encontrado: crear/configurar un bucket de prueba en esta cuenta.") from None
        if code in ("403", "AccessDenied"):
            raise ConfigurationError("Bucket sin acceso o de otro propietario; un 403 no confirma que no exista.") from None
        raise
    return s3, bucket, account


def upload(s3, bucket, account, export, run_id):
    key = f"raw/{export.name}/run_id={run_id}/{export.path.name}"
    s3.upload_file(str(export.path), bucket, key, ExtraArgs={
        "ExpectedBucketOwner": account,
        "ContentType": "text/csv; charset=utf-8",
        "Metadata": {"rows": str(export.rows), "run-id": run_id},
    })
    head = s3.head_object(Bucket=bucket, Key=key, ExpectedBucketOwner=account)
    if head["ContentLength"] != export.path.stat().st_size:
        raise RuntimeError("El tamaño del objeto S3 no coincide con el CSV local.")
    return f"s3://{bucket}/{key}"


def error_summary(exc):
    # Driver exceptions can contain connection strings; never print them verbatim.
    if isinstance(exc, ConfigurationError):
        return str(exc)
    response = getattr(exc, "response", {})
    code = response.get("Error", {}).get("Code") if isinstance(response, dict) else None
    return f"{type(exc).__name__}" + (f" (AWS: {code})" if code else "")


def execute(source, extractor, args):
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:8]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", run_id):
        raise ConfigurationError("run-id inválido; usar letras, números, guion o guion bajo.")
    directory = Path(args.output_dir) / source / run_id
    directory.mkdir(parents=True, exist_ok=False)
    report = {"source": source, "run_id": run_id, "mode": "local" if args.local_only else "s3",
              "status": "running", "exports": [], "warnings": []}
    try:
        target = None if args.local_only else aws_preflight()
        exports = extractor(directory, report["warnings"])
        for export in exports:
            report["exports"].append({"dataset": export.name, "rows": export.rows,
                                      "local_file": str(export.path), "s3_uri": None})
            if export.rows == 0:
                report["warnings"].append(f"{export.name}: fuente vacía (CSV solo con cabecera).")
        if target:
            s3, bucket, account = target
            for export, entry in zip(exports, report["exports"]):
                entry["s3_uri"] = upload(s3, bucket, account, export, run_id)
            report["aws_account"] = account
        report["status"] = "completed"
        # Completion marker goes outside raw so it is never read as tabular data.
        if target:
            key = f"_manifests/{source}/{run_id}.json"
            s3.put_object(Bucket=bucket, Key=key, ExpectedBucketOwner=account,
                          ContentType="application/json", Body=json.dumps(report, ensure_ascii=False).encode("utf-8"))
            report["manifest_s3_uri"] = f"s3://{bucket}/{key}"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = error_summary(exc)
    (directory / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "completed" else 1


def main(source, extractor):
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-only", action="store_true", help="Extraer CSV sin contactar AWS")
    parser.add_argument("--check-aws", action="store_true", help="Solo verificar token, cuenta y bucket")
    parser.add_argument("--output-dir", default=os.environ.get("OUTPUT_DIR", "reports"))
    parser.add_argument("--run-id", default=os.environ.get("INGESTION_RUN_ID") or None)
    parser.add_argument("--env-file", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.env_file:
            from dotenv import load_dotenv
            for path in args.env_file:
                if not Path(path).is_file():
                    raise ConfigurationError("No existe un archivo indicado en --env-file.")
                load_dotenv(path, override=False)
        if args.check_aws:
            _, bucket, account = aws_preflight()
            print(json.dumps({"status": "aws_verified", "bucket": bucket, "account": account}))
            return 0
        return execute(source, extractor, args)
    except Exception as exc:
        print(json.dumps({"source": source, "status": "failed", "error": error_summary(exc)}))
        return 1
