from extractor import extraer_pasajeros, extraer_tarjetas
from uploader import subir_a_s3
from config import settings


def run():
    print("Extrayendo pasajeros de MS1 (PostgreSQL)...")
    df_pasajeros = extraer_pasajeros()
    print(f"{len(df_pasajeros)} pasajeros extraídos.")
    subir_a_s3(df_pasajeros, settings.S3_BUCKET, prefix="pasajeros")

    print("Extrayendo tarjetas de MS1 (PostgreSQL)...")
    df_tarjetas = extraer_tarjetas()
    print(f"{len(df_tarjetas)} tarjetas extraídas.")
    subir_a_s3(df_tarjetas, settings.S3_BUCKET, prefix="tarjetas")

    print("Listo.")


if __name__ == "__main__":
    run()