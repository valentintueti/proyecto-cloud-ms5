from extractor import extraer_pasajeros_y_tarjetas
from uploader import subir_a_s3
from config import settings


def run():
    print("Extrayendo datos de MS1 (PostgreSQL)...")
    df = extraer_pasajeros_y_tarjetas()
    print(f"{len(df)} filas extraídas.")

    print(f"Subiendo a s3://{settings.S3_BUCKET}/ms1_pasajeros/...")
    subir_a_s3(df, settings.S3_BUCKET, prefix="ms1_pasajeros")
    print("Listo.")


if __name__ == "__main__":
    run()