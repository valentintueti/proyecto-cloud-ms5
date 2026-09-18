import csv
from common import ConfigurationError, Export, required

SERVICIOS_COLUMNS = ["id", "ruta_id", "ruta_nombre", "ruta_sentido", "fecha", "hora_inicio", "hora_fin"]
PARADEROS_COLUMNS = ["servicio_id", "paradero_id", "paradero_nombre", "orden"]


def flatten_services(directory, services, routes, stops, warnings):
    """Preserve every service and every nested occurrence, even orphan references."""
    service_path = directory / "servicios.csv"
    stop_path = directory / "servicio_paraderos.csv"
    service_count = stop_count = missing_route = missing_stop = 0
    with service_path.open("w", encoding="utf-8", newline="") as sf, stop_path.open("w", encoding="utf-8", newline="") as pf:
        service_writer = csv.writer(sf, lineterminator="\n")
        stop_writer = csv.writer(pf, lineterminator="\n")
        service_writer.writerow(SERVICIOS_COLUMNS)
        stop_writer.writerow(PARADEROS_COLUMNS)
        for service in services:
            service_id = str(service["_id"])
            route_id = service.get("ruta_id")
            route = routes.get(str(route_id), {})
            if not route:
                missing_route += 1
            service_writer.writerow([service_id, route_id, route.get("nombre"), route.get("sentido"),
                                     service.get("fecha"), service.get("hora_inicio"), service.get("hora_fin")])
            service_count += 1
            for entry in service.get("paraderos", []) or []:
                stop_id = entry.get("paradero_id")
                stop = stops.get(str(stop_id), {})
                if not stop:
                    missing_stop += 1
                stop_writer.writerow([service_id, stop_id, stop.get("nombre"), entry.get("orden")])
                stop_count += 1
    if missing_route:
        warnings.append(f"{missing_route} servicios con ruta ausente; nombre/sentido vacíos, filas conservadas.")
    if missing_stop:
        warnings.append(f"{missing_stop} referencias a paradero ausente; nombre vacío, filas conservadas.")
    return [Export("servicios", service_path, service_count), Export("servicio_paraderos", stop_path, stop_count)]


def extraer_servicios(directory, warnings):
    from pymongo import MongoClient
    uri, database = required("MONGO_URI"), required("DB_NAME")
    with MongoClient(uri, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000, socketTimeoutMS=60000) as client:
        db = client[database]
        # A misspelled DB/collection must not be reported as a successful empty export.
        if "servicios" not in db.list_collection_names():
            raise ConfigurationError("No existe la colección servicios en la BD configurada.")
        routes = {str(doc["_id"]): doc for doc in db.rutas.find({}, {"nombre": 1, "sentido": 1})}
        stops = {str(doc["_id"]): doc for doc in db.paraderos.find({}, {"nombre": 1})}
        with db.servicios.find({}).batch_size(2000) as services:
            return flatten_services(directory, services, routes, stops, warnings)
