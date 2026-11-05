"""Configuración centralizada: URLs, rutas de salida, selectores y política de reintentos."""

from __future__ import annotations

from pathlib import Path
from typing import Final

ORDER_URL: Final = "https://robotsparebinindustries.com/#/robot-order"
ORDERS_CSV_URL: Final = "https://robotsparebinindustries.com/orders.csv"

OUTPUT_DIR: Final = Path("output")
RECEIPTS_DIR: Final = OUTPUT_DIR / "receipts"
SCREENSHOTS_DIR: Final = OUTPUT_DIR / "screenshots"
ERRORS_DIR: Final = OUTPUT_DIR / "errors"
ORDERS_FILE: Final = OUTPUT_DIR / "orders.csv"
ARCHIVE_FILE: Final = OUTPUT_DIR / "receipts.zip"

# El sitio de práctica falla a propósito al enviar algunos pedidos: se reintenta.
SUBMIT_ATTEMPTS: Final = 5


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
