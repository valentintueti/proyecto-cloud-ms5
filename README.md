# MS5: tres ingestas independientes

Alcance: lectura directa de PostgreSQL, MongoDB y MySQL, generación de CSV y
subida al bucket S3 de prueba del Learner Lab personal. No crea Athena ni vistas.

## Estructura

`ingesta/docker-compose.yml` define exactamente `ingesta-ms1`, `ingesta-ms2`
y `ingesta-ms3`. Cada servicio tiene su Dockerfile, dependencias y extractor.
`ingesta/common.py` concentra configuración, CSV, verificación AWS, subida y
reportes; reemplaza los antiguos `config.py`/`uploader.py` exclusivos de MS1.
Los Dockerfiles ahora se construyen con **contexto `ingesta/`**, no desde la
carpeta individual, para incorporar ese módulo compartido.

Son trabajos batch de una ejecución: **Exited (0) significa éxito**. No son
servidores permanentes ni se reinician automáticamente. Un error termina con 1.

## Conexiones y credenciales

Desde `ingesta/`, copiar sin sobrescribir archivos ya configurados:

```sh
cp -n aws.env.example aws.env
cp -n ms1.env.example ms1.env
cp -n ms2.env.example ms2.env
cp -n ms3.env.example ms3.env
```

Durante esta sesión se dejaron estas cuatro copias locales con los campos
pendientes; están excluidas de Git y del contexto Docker.

- `ms1.env`: mismos `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  usados por MS1. No se inventan ni se usan credenciales por defecto.
- `ms2.env`: mismos `MONGO_URI`, `DB_NAME` usados por MS2.
- `ms3.env`: mismos cinco `DB_*` usados por MS3.
- `aws.env`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
  renovados desde un Learner Lab **personal** activo; `AWS_REGION`, `S3_BUCKET`
  y `AWS_EXPECTED_ACCOUNT_ID` (los 12 dígitos de esa cuenta personal).

Un `.env` de Docker Compose para interpolación no basta para inyectar todas
las variables: este Compose carga explícitamente los cuatro archivos anteriores
con `env_file`. No imprimir `docker compose config` con credenciales reales;
para enumerar servicios usar `config --services`.

El host de BD debe ser alcanzable **desde la VM/contenedor de ingesta**:
`localhost` dentro del contenedor no es la VM de BD. Para bases en el host de
Docker local se dispone de `host.docker.internal`; en AWS usar el DNS/IP privado
real de la VM de bases de datos y su conectividad existente. No se conecta a
redes de otros proyectos automáticamente.

## Ejecutar contra el bucket personal

```sh
docker compose config --services
docker compose build
docker compose run --rm ingesta-ms1 --check-aws
docker compose run --rm ingesta-ms2 --check-aws
docker compose run --rm ingesta-ms3 --check-aws
docker compose up --force-recreate
docker compose ps -a
```

Todos los jobs repiten el preflight antes de extraer: Boto3 debe encontrar las
tres partes de las credenciales temporales, STS debe responder con la cuenta
esperada y S3 debe aceptar `HeadBucket` con `ExpectedBucketOwner` igual a esa
cuenta. Un token expirado, otra cuenta o un bucket inaccesible abortan antes
de leer/subir datos. `--check-aws` no escribe ni crea buckets. Un 403 puede
ser falta de permisos o propietario distinto: no se interpreta como ausencia.
Un 404 requiere revisar el nombre y crear/configurar el bucket de prueba.
La prueba definitiva de permisos de escritura es la subida, no `HeadBucket`.

Para preparar CSV sin usar AWS:

```sh
docker compose run --rm ingesta-ms1 --local-only
docker compose run --rm ingesta-ms2 --local-only
docker compose run --rm ingesta-ms3 --local-only
```

También se puede ejecutar Python localmente tras instalar las dependencias de
cada extractor. Ejemplo desde `ingesta/`:

```sh
python -m pip install -r ingesta-ms1/requirements.txt
python ingesta-ms1/src/main.py --env-file aws.env --env-file ms1.env --check-aws
python ingesta-ms1/src/main.py --env-file aws.env --env-file ms1.env
```

Variables del proceso prevalecen sobre `--env-file`. En Docker los perfiles AWS
del host no se montan automáticamente; para este flujo se usan las credenciales
temporales de `aws.env`. Nunca guardar claves en el código ni en la imagen.

## Salidas y conteos

| Fuente | CSV | Prefijo S3 | Comportamiento |
|---|---|---|---|
| MS1 | pasajeros.csv | raw/pasajeros/ | SELECT * de pasajero; todos los registros/columnas |
| MS1 | tarjetas.csv | raw/tarjetas/ | SELECT * de tarjeta; independiente de pasajeros |
| MS2 | servicios.csv | raw/servicios/ | Todos los servicios; nombre/sentido desde rutas |
| MS2 | servicio_paraderos.csv | raw/servicio_paraderos/ | Una fila por cada ocurrencia anidada; nombre desde paraderos |
| MS3 | viajes.csv | raw/viajes/ | SELECT * de viaje |
| MS3 | pagos.csv | raw/pagos/ | SELECT * de Pago/pago solo si la tabla existe |

Cabeceras exactas de MS2:

```text
id,ruta_id,ruta_nombre,ruta_sentido,fecha,hora_inicio,hora_fin
servicio_id,paradero_id,paradero_nombre,orden
```

Las tablas SQL se leen sin LIMIT y con snapshot de solo lectura; PostgreSQL
procesa lotes de 2.000 y MySQL usa cursor sin buffer. CSV UTF-8, cabecera,
escapado estándar y sin conversión de importes decimales a float. Tablas vacías
generan cabecera y advertencia; no se confunden con una tabla inexistente.
MongoDB recorre el cursor completo; rutas/paraderos se cargan para resolver
referencias. Las referencias huérfanas conservan sus filas y producen una
advertencia con nombres vacíos. MongoDB no proporciona en este job un snapshot
transaccional entre las tres colecciones: para una foto estable evitar cambios
concurrentes durante la ingesta. Tampoco hay snapshot distribuido entre fuentes.

Pago ausente no bloquea Viaje; un error de conexión/permisos no se trata como
"Pago ausente". Su presencia se consulta en `information_schema` de la BD real,
incluyendo nombres `Pago`/`pago`; no se deduce del repositorio de MS3.

Cada ejecución usa una carpeta nueva para no sobrescribir extracciones:

```text
s3://<S3_BUCKET>/raw/<dataset>/run_id=<run-id>/<dataset>.csv
s3://<S3_BUCKET>/_manifests/ms1/<run-id>.json
```

Se puede fijar un identificador común con `INGESTION_RUN_ID` antes de iniciar
los tres servicios; debe ser nuevo para cada ejecución. Si se vuelve a ingerir
el 100%, cada run representa otra **foto completa**: no sumar snapshots como
si fueran datos incrementales. No hay promoción automática de un snapshot.

Los CSV y `manifest.json` quedan también en `ingesta/reports/msN/<run-id>/`.
El manifiesto registra filas por CSV, rutas S3 realmente subidas, advertencias
y resultado. Un manifiesto completado en S3 se escribe solo después de subir y
verificar el tamaño de todos los CSV del job. Si falla a mitad, puede haber
objetos parciales; el manifiesto local los distingue y no hay marcador de éxito.
Los errores se sanitizan para no mostrar contraseñas/cadenas de conexión.

## Pruebas reproducibles, sin fuentes reales ni AWS

Los fixtures están claramente separados bajo `ingesta/tests/`. El Compose de
prueba crea PostgreSQL, MongoDB y MySQL en una red propia, sin puertos publicados
y sin conectarse a `transport-backend-net` ni a otros contenedores existentes.

Desde `ingesta/`:

```sh
docker compose -f tests/compose.yml build ms1 ms2 ms3
docker compose -f tests/compose.yml up -d --wait postgres mongo mysql
docker compose -f tests/compose.yml run --rm ms1
docker compose -f tests/compose.yml run --rm ms2
docker compose -f tests/compose.yml run --rm ms3
docker compose -f tests/compose.yml exec -T -e MYSQL_PWD=fixture-only mysql mysql -u fixture fixture < tests/fixtures/pago.sql
docker compose -f tests/compose.yml run --rm ms3
docker compose -f tests/compose.yml down -v
```

La redirección de SQL del ejemplo es para shells POSIX. En PowerShell usar
`Get-Content -Raw tests/fixtures/pago.sql | docker compose ... exec -T ...`.
La segunda ejecución de MS3 comprueba Pago presente; la primera, Pago ausente.
No ejecutar el script de creación de Pago sobre una BD real.

Pruebas unitarias (requieren Boto3 instalado, sin llamadas AWS):

```sh
python -m unittest discover -s tests -v
```

Ver [VALIDACION_INGESTA.md](VALIDACION_INGESTA.md) para resultados y pendientes
de la sesión. Los conteos sintéticos no son evidencia del volumen de las bases
del proyecto ni una prueba de subida real a S3.
