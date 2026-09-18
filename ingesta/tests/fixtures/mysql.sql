USE fixture;
CREATE TABLE viaje (
  id int PRIMARY KEY, pasajero_id int NOT NULL, servicio_id varchar(40), tarjeta_id int,
  fecha_hora datetime, paradero_origen_id varchar(40), paradero_final_id varchar(40), estado varchar(20)
);
INSERT INTO viaje VALUES
 (1, 1, 's1', 1, '2026-09-16 08:00:00', 'p1', NULL, 'en_curso'),
 (2, 2, 's1', 2, '2026-09-16 08:30:00', 'p1', 'p2', 'finalizado');
-- Pago intentionally absent to exercise the optional-table path.
