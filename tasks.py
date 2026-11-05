"""Tarea Robocorp: pedir robots en RobotSpareBin Industries y archivar los recibos.

Flujo por cada fila del CSV del día:
cerrar aviso → llenar formulario → vista previa → enviar (con reintentos) →
recibo en PDF → captura del robot incrustada en el PDF → "pedir otro".
Al final todos los recibos se comprimen en ``output/receipts.zip``.

Un pedido que falla no detiene el lote: se guarda evidencia (captura de pantalla), se registra
y el robot continúa con el siguiente. Si hubo fallas, la tarea termina en error con el resumen.
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from robocorp import browser, log
from robocorp.tasks import task

from robot.config import ARCHIVE_FILE, ERRORS_DIR, ORDERS_CSV_URL, ORDERS_FILE, RECEIPTS_DIR
from robot.order_page import OrderPage
from robot.orders import Order, download_orders
from robot.receipts import archive_receipts, embed_screenshot, screenshot_path, store_receipt_as_pdf
from robot.retry import StepFailedError


@task
def order_robots_from_robotsparebin() -> None:
    """Pide los robots del CSV del día y guarda un recibo PDF por pedido."""
    browser.configure(slowmo=100)
    orders = download_orders(ORDERS_CSV_URL, ORDERS_FILE)
    log.info(f"{len(orders)} pedidos por procesar")

    page = OrderPage(browser.page())
    page.open()
    failures: dict[int, str] = {}

    for order in orders:
        with log.suppress_variables():  # los datos del pedido no se vuelcan completos al log
            try:
                process_order(page, order)
            except (StepFailedError, PlaywrightTimeoutError) as error:
                failures[order.number] = str(error)
                evidence = page.screenshot_page(ERRORS_DIR / f"order_{order.number}.png")
                log.warn(f"Pedido {order.number} falló: {error}. Evidencia: {evidence}")
                page.reset()

    archive_receipts(RECEIPTS_DIR, ARCHIVE_FILE)
    log.info(f"Procesados {len(orders) - len(failures)}/{len(orders)} pedidos · {ARCHIVE_FILE}")
    if failures:
        raise RuntimeError(f"{len(failures)} pedidos fallaron: {failures}")


def process_order(page: OrderPage, order: Order) -> None:
    page.close_modal()
    page.fill(order)
    page.preview()
    attempts = page.submit(on_retry=lambda n: log.warn(f"Pedido {order.number}: reintento {n}"))
    log.info(f"Pedido {order.number} enviado en el intento {attempts}")

    pdf_file = store_receipt_as_pdf(page.receipt_html(), order.number)
    screenshot = page.screenshot_robot(screenshot_path(order.number))
    embed_screenshot(screenshot, pdf_file)
    page.order_another()
