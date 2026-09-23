from extractor import extraer_rutas, extraer_paraderos, extraer_servicios
from uploader import subir_a_s3
from config import settings


def run():
    for nombre, extractor in [
        ("rutas", extraer_rutas),
        ("paraderos", extraer_paraderos),
        ("servicios", extraer_servicios),
    ]:
        print(f"Extrayendo {nombre} de MS2 (MongoDB)...")
        data = extractor()
        print(f"{len(data)} documentos extraídos.")
        subir_a_s3(data, settings.S3_BUCKET, prefix=nombre)

    print("Listo.")


if __name__ == "__main__":
    run()