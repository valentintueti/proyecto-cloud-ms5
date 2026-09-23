import boto3
import json
from config import settings


def subir_a_s3(data: list[dict], bucket: str, prefix: str):
    key = f"{prefix}/data.json"

    lineas = "\n".join(json.dumps(doc, ensure_ascii=False) for doc in data)

    s3 = boto3.client("s3", region_name=settings.AWS_REGION)
    s3.put_object(Bucket=bucket, Key=key, Body=lineas.encode("utf-8"))
    print(f"Subido: s3://{bucket}/{key}")