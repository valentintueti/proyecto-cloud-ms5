CREATE TABLE pasajero (
  id bigint PRIMARY KEY, nombre text NOT NULL, fecha_nacimiento date,
  sexo varchar(20), distrito text
);
CREATE TABLE tarjeta (
  id bigint PRIMARY KEY, pasajero_id bigint REFERENCES pasajero(id),
  fecha_emision date, fecha_vencimiento date, tipo varchar(40), saldo numeric(15,2)
);
INSERT INTO pasajero
SELECT n, 'Pasajero sintético ' || n, '2000-01-01'::date, 'MASCULINO', 'Fixture'
FROM generate_series(1, 2005) n;
INSERT INTO tarjeta
SELECT n, n, '2026-09-16'::date, NULL, 'REGULAR', 12.34 FROM generate_series(1, 2004) n;
INSERT INTO tarjeta VALUES (2005, 1, '2026-09-16', NULL, 'REGULAR', 123456789.12);
-- Passenger 2005 has no card; passenger 1 has two. Neither may be lost/duplicated.
