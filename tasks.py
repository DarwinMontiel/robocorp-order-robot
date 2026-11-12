"""Tarea Robocorp: pedir robots en RobotSpareBin Industries y archivar los recibos.

Flujo por cada fila válida del CSV del día:
cerrar aviso → llenar formulario → vista previa → enviar (con reintentos) →
recibo en PDF → captura del robot incrustada en el PDF → "pedir otro".
Al final los recibos de esta ejecución se comprimen en ``output/recibos.zip`` y se escribe el
reporte de turno en ``output/resumen.md``.

Ningún caso detiene el lote: una fila inválida se aparta (error de negocio) y un pedido que
falla tras los reintentos deja evidencia (error de sistema). Si hubo alguno, la tarea termina
en error remitiendo al resumen, para que se reprocese solo lo pendiente.
"""

from __future__ import annotations

from datetime import datetime

from robocorp import browser, log
from robocorp.tasks import task

from robot.config import ARCHIVE_FILE, ORDERS_CSV_URL, ORDERS_FILE, RUN_DIRS, SUMMARY_FILE
from robot.order_page import OrderPage
from robot.orders import Order, download_orders
from robot.receipts import (
    archive_receipts,
    embed_screenshot,
    evidence_path,
    prepare_output,
    receipt_path,
    screenshot_path,
    store_receipt_as_pdf,
)
from robot.report import Failure, ShiftReport, describe_failure


@task
def pedir_robots_del_dia() -> None:
    """Pide los robots del CSV del día y guarda un recibo PDF por pedido."""
    browser.configure(slowmo=100)
    prepare_output(RUN_DIRS)
    batch = download_orders(ORDERS_CSV_URL, ORDERS_FILE)
    report = ShiftReport(started_at=datetime.now(), rejected=batch.rejected)
    for row in batch.rejected:
        log.warn(f"Línea {row.line} apartada (error de negocio): {row.reason}")
    log.info(f"{len(batch.orders)} pedidos por procesar")

    page = OrderPage(browser.page())
    page.open()

    for order in batch.orders:
        with log.suppress_variables():  # los datos del pedido no se vuelcan al log
            try:
                report.delivered[order.number] = process_order(page, order)
            except Exception as error:  # error de sistema: se documenta y el lote sigue
                reason = describe_failure(error)
                evidence = page.screenshot_page(evidence_path(order.number))
                report.failed[order.number] = Failure(reason=reason, evidence=evidence)
                log.warn(f"Pedido {order.number} falló: {reason}. Evidencia: {evidence}")
                page.reset()

    archive_receipts([receipt_path(n) for n in report.delivered], ARCHIVE_FILE)
    SUMMARY_FILE.write_text(report.render(), encoding="utf-8")
    log.info(f"{report.headline()} · {ARCHIVE_FILE} · {SUMMARY_FILE}")
    if not report.clean:
        raise RuntimeError(f"Turno con pendientes: {report.headline()}. Ver {SUMMARY_FILE}")


def process_order(page: OrderPage, order: Order) -> int:
    """Procesa un pedido y devuelve el intento en que el envío tuvo éxito."""
    page.close_modal()
    page.fill(order)
    page.preview()
    attempts = page.submit(on_retry=lambda n: log.warn(f"Pedido {order.number}: reintento {n}"))
    log.info(f"Pedido {order.number} enviado en el intento {attempts}")

    pdf_file = store_receipt_as_pdf(page.receipt_html(), order.number)
    screenshot = page.screenshot_robot(screenshot_path(order.number))
    embed_screenshot(screenshot, pdf_file)
    page.order_another()
    return attempts
