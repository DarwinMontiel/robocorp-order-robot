from __future__ import annotations

import zipfile
from pathlib import Path

from robot.receipts import (
    archive_receipts,
    evidence_path,
    prepare_output,
    receipt_path,
    screenshot_path,
)


def test_deliverables_have_stable_spanish_names() -> None:
    assert receipt_path(7).as_posix() == "output/recibos/recibo_7.pdf"
    assert screenshot_path(7).as_posix() == "output/capturas/robot_7.png"
    assert evidence_path(7).as_posix() == "output/errores/pedido_7.png"


def test_prepare_output_removes_files_from_previous_runs(tmp_path: Path) -> None:
    receipts, errors = tmp_path / "recibos", tmp_path / "errores"
    receipts.mkdir()
    (receipts / "recibo_99.pdf").write_bytes(b"de ayer")

    prepare_output([receipts, errors])

    assert receipts.is_dir()
    assert errors.is_dir()
    assert list(receipts.iterdir()) == []


def test_archive_contains_only_the_receipts_of_this_run(tmp_path: Path) -> None:
    folder = tmp_path / "recibos"
    folder.mkdir()
    today = [folder / "recibo_2.pdf", folder / "recibo_10.pdf"]
    for receipt in today:
        receipt.write_bytes(b"%PDF")
    (folder / "recibo_99.pdf").write_bytes(b"de ayer")  # no se entregó hoy

    archive = archive_receipts(today, tmp_path / "recibos.zip")

    with zipfile.ZipFile(archive) as bundle:
        assert bundle.namelist() == ["recibo_2.pdf", "recibo_10.pdf"]
