"""Recibos: PDF con la imagen del robot y archivo ZIP final (RPA Framework)."""

from __future__ import annotations

from pathlib import Path

from robot.config import RECEIPTS_DIR, SCREENSHOTS_DIR


def receipt_path(order_number: int) -> Path:
    return RECEIPTS_DIR / f"receipt_{order_number}.pdf"


def screenshot_path(order_number: int) -> Path:
    return SCREENSHOTS_DIR / f"robot_{order_number}.png"


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


def archive_receipts(folder: Path, archive: Path) -> Path:
    from RPA.Archive import Archive

    Archive().archive_folder_with_zip(folder=str(folder), archive_name=str(archive))
    return archive
