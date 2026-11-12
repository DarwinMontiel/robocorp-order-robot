"""Recibos: PDF con la imagen del robot, limpieza de la salida y ZIP final."""

from __future__ import annotations

import shutil
import zipfile
from collections.abc import Iterable
from pathlib import Path

from robot.config import ERRORS_DIR, RECEIPTS_DIR, SCREENSHOTS_DIR


def receipt_path(order_number: int) -> Path:
    return RECEIPTS_DIR / f"recibo_{order_number}.pdf"


def screenshot_path(order_number: int) -> Path:
    return SCREENSHOTS_DIR / f"robot_{order_number}.png"


def evidence_path(order_number: int) -> Path:
    return ERRORS_DIR / f"pedido_{order_number}.png"


def prepare_output(folders: Iterable[Path]) -> None:
    """Vacía las carpetas de la ejecución para que no se mezclen recibos de días anteriores."""
    for folder in folders:
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)


def store_receipt_as_pdf(html: str, order_number: int) -> Path:
    from RPA.PDF import PDF

    path = receipt_path(order_number)
    path.parent.mkdir(parents=True, exist_ok=True)
    PDF().html_to_pdf(html, str(path))
    return path


def embed_screenshot(screenshot: Path, pdf_file: Path) -> None:
    from RPA.PDF import PDF

    PDF().add_watermark_image_to_pdf(
        image_path=str(screenshot), source_path=str(pdf_file), output_path=str(pdf_file)
    )


def archive_receipts(receipts: Iterable[Path], archive: Path) -> Path:
    """Comprime solo los recibos entregados en esta ejecución, en el orden en que se generaron."""
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for receipt in receipts:
            bundle.write(receipt, arcname=receipt.name)
    return archive
