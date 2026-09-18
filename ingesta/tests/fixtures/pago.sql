USE fixture;
CREATE TABLE Pago (id int PRIMARY KEY, viaje_id int UNIQUE REFERENCES viaje(id), monto decimal(10,2));
INSERT INTO Pago VALUES (1, 1, 2.50), (2, 2, 1.25);
