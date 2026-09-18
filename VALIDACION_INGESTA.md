# Validación de ingestas — 2026-09-16

## Estado inicial confirmado antes de editar

- Únicamente existía `ingesta/ingesta-ms1`: Dockerfile, requirements y cuatro
  archivos Python; `extractor.py` tenía cero bytes.
- `main.py` importaba `extraer_pasajeros_y_tarjetas`, que no estaba definida.
- Uploader limitado a un CSV en `ms1_pasajeros/fecha=.../data.csv`.
- No existían Compose de ingesta ni extractores MS2/MS3.
- No había conexiones reales ni bucket en archivos `.env` de este repositorio.

## Resultado técnico verificado

| Comprobación | Resultado |
|---|---|
| Compose principal | Exactamente 3 servicios: ingesta-ms1, ingesta-ms2, ingesta-ms3 |
| Build Docker MS1 | Correcto |
| Build Docker MS2 | Correcto |
| Build Docker MS3 | Correcto |
| Pruebas unitarias | 12/12 correctas dentro de Docker sin red |
| CSV grande | 20.001 filas sintéticas preservadas, sin truncamiento ni pérdida de precisión decimal |
| Arranque Compose principal | Los tres jobs arrancaron; terminaron con código 1 y `Falta configurar S3_BUCKET.` |
| PostgreSQL real del proyecto | Pendiente de conexión autorizada |
| MongoDB real del proyecto | Pendiente de conexión autorizada |
| MySQL real del proyecto | Pendiente de conexión autorizada |
| Credenciales personales AWS | No disponibles en entorno/perfiles inspeccionados; Boto3 del contenedor sin configuración tampoco encontró credenciales |
| Existencia del bucket personal | No verificable: no hay nombre ni credenciales disponibles |
| Archivos escritos en S3 | Ninguno |

Docker era inaccesible desde el entorno restringido, pero se verificó su motor
28.0.4 y se realizaron builds/pruebas con acceso autorizado fuera de ese entorno.
Los contenedores detectados de `Cloud/Proyecto/Proyecto-AWS-1` **no se usaron**:
el usuario indicó expresamente que las fuentes serían otras conexiones.

## Integración aislada con motores reales y datos sintéticos

Se crearon tres bases desechables en la red `cs2032-ingesta-test_default`, sin
puertos publicados ni acceso a la red de los otros proyectos. No se cargaron
datos sintéticos en bases del proyecto ni se contactó AWS.

| Ejecución de prueba | CSV | Filas | Resultado |
|---|---|---:|---|
| MS1 PostgreSQL | pasajeros.csv | 2.005 | Exportación completa; incluye pasajero sin tarjeta |
| MS1 PostgreSQL | tarjetas.csv | 2.005 | Incluye dos tarjetas para un pasajero y saldo decimal grande |
| MS2 MongoDB | servicios.csv | 3 | Incluye servicio sin paraderos y servicio con ruta inexistente |
| MS2 MongoDB | servicio_paraderos.csv | 3 | Conserva referencia huérfana con nombre vacío |
| MS3 MySQL sin Pago | viajes.csv | 2 | Éxito; advertencia explícita de Pago pendiente |
| MS3 MySQL con Pago | viajes.csv | 2 | Éxito |
| MS3 MySQL con Pago | pagos.csv | 2 | Éxito; detectó tabla llamada `Pago` con mayúscula |

**Estos conteos NO corresponden a las bases reales del usuario.** No demuestran
20.000 registros de negocio ni una subida exitosa a S3.

Evidencia local (rutas relativas a este repositorio, excluidas de Git):

- `ingesta/reports/fixtures/ms1/20260916T204235371143Z-f3f39010/`
- `ingesta/reports/fixtures/ms2/20260916T204237862946Z-1b658489/`
- `ingesta/reports/fixtures/ms3/20260916T204241034251Z-ad7bd707/`
- `ingesta/reports/fixtures/ms3/20260916T204311113929Z-8bfb132a/`

Cada carpeta contiene los CSV y un `manifest.json` con estado, conteos y
advertencias. Los manifiestos del intento de ejecución real están bajo
`ingesta/reports/ms1`, `ms2`, `ms3`: no contienen exports ni URI S3 porque el
preflight abortó antes de leer cualquier fuente.

Al terminar se retiraron los tres contenedores de BD de prueba, sus volúmenes
y su red con el Compose de tests. Se conservaron imágenes, CSV y manifiestos.
Los tres contenedores del Compose principal quedan detenidos con código 1
para que su diagnóstico pueda consultarse con `docker compose logs`.

## Pendientes para completar la ejecución solicitada

1. Conexiones autorizadas de MS1, MS2 y MS3 (o acceso a la VM de ingesta).
2. Credenciales temporales vigentes de Learner Lab personal, región y account ID.
3. Nombre del bucket S3 de prueba. Una vez autenticado se verificará si existe;
   no se ha asumido que haya que crear uno ni se ha creado un bucket.
4. Ejecutar el Compose con esa configuración y reemplazar el estado pendiente
   por conteos reales y URI completas verificadas.

**Pago real sigue pendiente de verificar.** No existe en el código MS3 revisado,
pero solo consultar el catálogo de la BD indicada permitirá confirmar si fue
creado por otro medio. El extractor ya maneja ambos casos sin bloquear Viaje
cuando Pago no existe.

Las URI previstas tienen la forma `s3://<bucket>/raw/<dataset>/run_id=<run>/<dataset>.csv`.
No son objetos existentes. No se implementaron Athena ni vistas.
