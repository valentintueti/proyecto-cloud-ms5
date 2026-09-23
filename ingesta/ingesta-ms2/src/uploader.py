import boto3
import json
from datetime import date
from config import settings


def subir_a_s3(data: list[dict], bucket: str, prefix: str):
    hoy = date.today().isoformat()
    key = f"{prefix}/fecha={hoy}/data.json"

    s3 = boto3.client("s3", region_name=settings.AWS_REGION)
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, ensure_ascii=False).encode("utf-8"))
    print(f"Subido: s3://{bucket}/{key}")