from __future__ import annotations

from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from robot.orders import RejectedRow
from robot.report import Failure, ShiftReport, describe_failure
from robot.retry import StepFailedError

START = datetime(2026, 1, 5, 7, 0)


def test_summary_separates_system_and_business_errors() -> None:
    report = ShiftReport(
        started_at=START,
        delivered={1: 1, 3: 3, 4: 1},
        failed={
            2: Failure(
                "enviar pedido: sin éxito tras 5 intentos", Path("output/errores/pedido_2.png")
            )
        },
        rejected=[RejectedRow(line=6, reason="falta la columna «Legs»")],
    )

    text = report.render()

    assert report.total == 5
    assert report.retries == 2
    assert not report.clean
    assert report.headline() == "3/5 pedidos entregados · 1 fallidos · 1 filas apartadas"
    assert "Inicio: 2026-01-05 07:00" in text
    assert "| Reintentos usados | 2 |" in text
    assert (
        "| 2 | enviar pedido: sin éxito tras 5 intentos | `output/errores/pedido_2.png` |" in text
    )
    assert "| 6 | falta la columna «Legs» |" in text
    assert "Turno limpio" not in text


def test_a_clean_shift_says_so() -> None:
    report = ShiftReport(started_at=START, delivered={1: 1, 2: 2})

    assert report.clean
    assert "Turno limpio" in report.render()
    assert "## Fallidos" not in report.render()


def test_failure_reasons_are_short_and_do_not_echo_unknown_messages() -> None:
    timeout = PlaywrightTimeoutError("Timeout 30000ms exceeded.\nCall log:\n  - waiting for #order")
    assert describe_failure(timeout) == "el navegador agotó el tiempo de espera"
    assert describe_failure(StepFailedError("enviar pedido: sin éxito tras 5 intentos")) == (
        "enviar pedido: sin éxito tras 5 intentos"
    )
    assert describe_failure(ValueError("Calle Ficticia 742")) == (
        "ValueError: error de sistema inesperado"
    )
