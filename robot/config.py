"""Configuración centralizada: URLs, rutas de salida, selectores y política de reintentos."""

from __future__ import annotations

from pathlib import Path
from typing import Final

ORDER_URL: Final = "https://robotsparebinindustries.com/#/robot-order"
ORDERS_CSV_URL: Final = "https://robotsparebinindustries.com/orders.csv"

# Entregables en español: es lo que recibe quien usa el robot.
OUTPUT_DIR: Final = Path("output")
RECEIPTS_DIR: Final = OUTPUT_DIR / "recibos"
SCREENSHOTS_DIR: Final = OUTPUT_DIR / "capturas"
ERRORS_DIR: Final = OUTPUT_DIR / "errores"
ORDERS_FILE: Final = OUTPUT_DIR / "pedidos.csv"
ARCHIVE_FILE: Final = OUTPUT_DIR / "recibos.zip"
SUMMARY_FILE: Final = OUTPUT_DIR / "resumen.md"

# Carpetas que se vacían al iniciar: el ZIP del día solo lleva recibos de esta ejecución.
RUN_DIRS: Final = (RECEIPTS_DIR, SCREENSHOTS_DIR, ERRORS_DIR)

# El sitio de práctica falla a propósito al enviar algunos pedidos: se reintenta.
SUBMIT_ATTEMPTS: Final = 5
# Tiempo que se espera a que aparezca el recibo después de cada clic en "Order".
RECEIPT_WAIT_MS: Final = 3_000


class Selectors:
    """Selectores del formulario (un solo lugar para mantenerlos si el sitio cambia)."""

    MODAL_OK: Final = "button.btn-warning"
    HEAD: Final = "#head"
    BODY_RADIO: Final = 'input[name="body"][value="{value}"]'
    LEGS: Final = "input[placeholder='Enter the part number for the legs']"
    ADDRESS: Final = "#address"
    PREVIEW: Final = "#preview"
    ORDER: Final = "#order"
    RECEIPT: Final = "#receipt"
    ROBOT_PREVIEW_IMAGE: Final = "#robot-preview-image"
    ORDER_ANOTHER: Final = "#order-another"
