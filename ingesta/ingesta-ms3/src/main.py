from extractor import extraer_viajes, extraer_conexiones
from uploader import subir_a_s3
from config import settings


def run():
    print("Extrayendo viajes de MS3 (MySQL)...")
    viajes = extraer_viajes()
    print(f"{len(viajes)} viajes extraídos.")
    subir_a_s3(viajes, settings.S3_BUCKET, prefix="ms3_viajes")

    print("Extrayendo conexiones de MS3 (MySQL)...")
    conexiones = extraer_conexiones()
    print(f"{len(conexiones)} conexiones extraídas.")
    subir_a_s3(conexiones, settings.S3_BUCKET, prefix="ms3_conexiones")

    print("Listo.")


if __name__ == "__main__":
    run()