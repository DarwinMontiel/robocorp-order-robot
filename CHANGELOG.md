# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]

### Cambiado
- El repositorio pasa a llamarse `robot-pedidos-robocorp` (antes `robocorp-order-robot`).
- Entregables en español: `output/recibos/recibo_<n>.pdf`, `output/recibos.zip`,
  `output/capturas/`, `output/errores/pedido_<n>.png` y `output/pedidos.csv`.
- La tarea se llama «Pedir robots del día» (`pedir_robots_del_dia`).
- El README cuenta el flujo con un diagrama de secuencia y explica su relación con la cobranza.

### Corregido
- Una fila inválida del CSV ya no aborta el lote: se aparta como error de negocio y se informa.
- El envío espera de forma explícita al recibo y no vuelve a hacer clic si llegó tarde.
- El ZIP ya no incluye recibos de ejecuciones anteriores.
- Los mensajes de filas inválidas ya no vuelcan los valores de la fila al log.
- Una falla inesperada en un pedido ya no detiene el lote: queda como error de sistema.

### Agregado
- Reporte de turno en `output/resumen.md`.
- Pruebas del Page Object con una página falsa, de recibos, del ZIP y del reporte.
- Tipado estricto con mypy en CI.

## [1.0.0] · 2025

- Robot del Nivel I de la certificación Robocorp: pedidos, recibos PDF y ZIP.
