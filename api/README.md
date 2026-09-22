# MS5: API Rest Consultas Analiticas

El microservicio analitico que pide el enunciado: sin base de datos propia,
ejecuta consultas Athena (sobre el catalogo Glue `transporte_metropolitano`
poblado por `../ingesta/`) y las expone como JSON por HTTP. Documentacion
interactiva (swagger-ui) en `/docs` una vez levantado.

No requiere ninguna VM de produccion para funcionar: corre local en Docker
igual que MS1-4, apuntando a Athena real con las credenciales del Learner
Lab. El frontend puede integrar contra `http://localhost:8084` desde ya.

## Configuracion

```sh
cp -n aws.env.example aws.env
cp -n athena.env.example athena.env
```

Completar `aws.env` con las credenciales temporales vigentes del Learner Lab
(las mismas de `../ingesta/aws.env`; se pueden copiar tal cual). `athena.env`
ya trae los valores correctos para el bucket/base de datos actuales — solo
hay que ajustarlo si cambia el nombre del bucket o de la base Glue.

## Ejecutar

```sh
docker compose up -d --build
curl http://localhost:8084/health
curl http://localhost:8084/analitica/demanda-por-ruta
```

Swagger UI: http://localhost:8084/docs

## Endpoints

| Endpoint | Corresponde a |
|---|---|
| `GET /health` | Chequeo de salud |
| `GET /analitica/demanda-por-ruta` | Consulta 1 |
| `GET /analitica/demanda-por-paradero` | Consulta 2 |
| `GET /analitica/demanda-por-hora` | Consulta 3 |
| `GET /analitica/evolucion-mensual` | Consulta 4 |
| `GET /analitica/paraderos-por-perfil` | Consulta 5 |
| `GET /analitica/concentracion-pasajeros` | Consulta 6 (Pareto) |
| `GET /analitica/saldo-flotante` | Consulta 7 |
| `GET /analitica/viajes-fuera-horario` | Consulta 8 |
| `GET /analitica/ingresos-por-ruta` | Vista `vista_ingresos_por_ruta` |

El SQL de cada endpoint es copia textual de lo ya validado en
`avance_consultas/ms5_consultas_athena_vistas.md` (`app/queries.py` no
reescribe nada, solo lo reutiliza).

## Notas

- Cada consulta puede tardar unos segundos: Athena no es instantaneo. Un
  timeout de 60s en `athena_client.py` devuelve HTTP 502 si tarda mas.
- Las vistas (`vista_viajes_completos`, `vista_ingresos_por_ruta`) ya existen
  en el catalogo Glue (se crearon manualmente en la consola de Athena); esta
  API no las vuelve a crear, solo las consulta.
- Si se recrea el catalogo apuntando a un bucket/cuenta AWS distinta (por
  ejemplo, la cuenta del compañero de deployment), solo hay que actualizar
  `athena.env` — el codigo no cambia.
