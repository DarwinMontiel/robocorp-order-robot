"""El Page Object contra una página falsa: sin navegador, pero con la semántica de Playwright."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from robot.config import Selectors
from robot.order_page import OrderPage
from robot.retry import StepFailedError


class FakePage:
    """Simula el envío.

    - ``rejections``: cuántos clics en «Order» rechaza el servidor (error de sistema).
    - ``late_by``: cuántas esperas del recibo vencen antes de que aparezca un envío aceptado.
    """

    def __init__(self, rejections: int = 0, late_by: int = 0) -> None:
        self.rejections = rejections
        self.late_by = late_by
        self.accepted = False
        self.visible: set[str] = set()
        self.clicks: list[str] = []
        self.waits: list[float] = []

    def is_visible(self, selector: str) -> bool:
        return selector in self.visible

    def click(self, selector: str) -> None:
        self.clicks.append(selector)
        if selector == Selectors.ORDER:
            if self.rejections:
                self.rejections -= 1
            else:
                self.accepted = True

    def locator(self, selector: str) -> FakePage:
        assert selector == Selectors.RECEIPT
        return self

    def wait_for(self, state: str, timeout: float) -> None:
        assert state == "visible"
        self.waits.append(timeout)
        if self.accepted and self.late_by:
            self.late_by -= 1
            self.visible.add(Selectors.RECEIPT)  # llega justo después de vencer la espera
            raise PlaywrightTimeoutError(f"Timeout {timeout}ms exceeded.")
        if not self.accepted:
            raise PlaywrightTimeoutError(f"Timeout {timeout}ms exceeded.")
        self.visible.add(Selectors.RECEIPT)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("robot.retry.time.sleep", lambda _: None)


def submit(fake: FakePage) -> int:
    return OrderPage(cast(Any, fake), receipt_wait_ms=50).submit()


def test_submit_retries_until_the_receipt_appears() -> None:
    fake = FakePage(rejections=2)

    assert submit(fake) == 3
    assert fake.clicks.count(Selectors.ORDER) == 3
    assert fake.waits == [50, 50, 50]  # espera explícita en cada intento


def test_a_late_receipt_is_not_submitted_twice() -> None:
    fake = FakePage(late_by=1)

    assert submit(fake) == 2
    assert fake.clicks.count(Selectors.ORDER) == 1  # el pedido ya estaba enviado


def test_submit_gives_up_after_the_configured_attempts() -> None:
    fake = FakePage(rejections=99)

    with pytest.raises(StepFailedError, match="enviar pedido: sin éxito tras 5 intentos"):
        submit(fake)
    assert fake.clicks.count(Selectors.ORDER) == 5


class BrokenPage:
    """Navegador que ya no responde: ni capturas ni recarga."""

    def screenshot(self, path: str, full_page: bool) -> None:
        raise PlaywrightTimeoutError("Timeout 30000ms exceeded.")

    def goto(self, url: str) -> None:
        raise PlaywrightTimeoutError("Timeout 30000ms exceeded.")


def test_recovering_from_a_failed_order_never_aborts_the_batch(tmp_path: Path) -> None:
    page = OrderPage(cast(Any, BrokenPage()))

    assert page.capture_evidence(tmp_path / "errores" / "pedido_2.png") is None
    assert page.reset() is False
