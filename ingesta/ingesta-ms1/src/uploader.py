import boto3
import io
from config import settings


def subir_a_s3(df, bucket: str, prefix: str):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)

    key = f"{prefix}/data.csv"

    s3 = boto3.client("s3", region_name=settings.AWS_REGION)
    s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    print(f"Subido: s3://{bucket}/{key}")