const fixture = db.getSiblingDB('fixture');
fixture.rutas.insertOne({_id: 'r1', nombre: 'Ruta, Norte', sentido: 'IDA'});
fixture.paraderos.insertMany([{_id: 'p1', nombre: 'Central'}, {_id: 'p2', nombre: 'Sur'}]);
fixture.servicios.insertMany([
  {_id: 's1', ruta_id: 'r1', fecha: '2026-09-16', hora_inicio: '08:00:00', hora_fin: '10:00:00',
   paraderos: [{paradero_id: 'p1', orden: 1}, {paradero_id: 'p2', orden: 2}]},
  {_id: 's2', ruta_id: 'r1', fecha: '2026-09-16', hora_inicio: '11:00:00', hora_fin: '12:00:00', paraderos: []},
  {_id: 's3', ruta_id: 'missing', fecha: '2026-09-16', hora_inicio: '13:00:00', hora_fin: '14:00:00',
   paraderos: [{paradero_id: 'missing', orden: 1}]}
]);
