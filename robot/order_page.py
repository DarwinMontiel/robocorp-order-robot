"""Page Object del formulario de pedidos: toda interacción con el navegador vive aquí."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from robot.config import ORDER_URL, RECEIPT_WAIT_MS, SUBMIT_ATTEMPTS, Selectors
from robot.orders import Order
from robot.retry import retry_until

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import Page


class OrderPage:
    def __init__(self, page: Page, receipt_wait_ms: int = RECEIPT_WAIT_MS) -> None:
        self.page = page
        self.receipt_wait_ms = receipt_wait_ms

    def open(self) -> None:
        self.page.goto(ORDER_URL)

    def close_modal(self) -> None:
        """El sitio muestra un aviso de derechos en cada pedido."""
        if self.page.is_visible(Selectors.MODAL_OK):
            self.page.click(Selectors.MODAL_OK)

    def fill(self, order: Order) -> None:
        self.page.select_option(Selectors.HEAD, order.head)
        self.page.click(Selectors.BODY_RADIO.format(value=order.body))
        self.page.fill(Selectors.LEGS, order.legs)
        self.page.fill(Selectors.ADDRESS, order.address)

    def preview(self) -> None:
        self.page.click(Selectors.PREVIEW)

    def submit(self, on_retry: Callable[[int], None] | None = None) -> int:
        """Envía el pedido; el servidor de práctica falla aleatoriamente, así que se reintenta."""
        return retry_until(
            action=self._click_order,
            succeeded=self.receipt_appeared,
            attempts=SUBMIT_ATTEMPTS,
            description="enviar pedido",
            on_retry=on_retry,
        )

    def _click_order(self) -> None:
        # Si el recibo llegó tarde, el pedido ya se envió: no se vuelve a hacer clic.
        if not self.page.is_visible(Selectors.RECEIPT):
            self.page.click(Selectors.ORDER)

    def receipt_appeared(self) -> bool:
        """Espera de forma explícita al recibo; ``is_visible`` responde sin esperar."""
        try:
            self.page.locator(Selectors.RECEIPT).wait_for(
                state="visible", timeout=self.receipt_wait_ms
            )
        except PlaywrightTimeoutError:
            return False
        return True

    def receipt_html(self) -> str:
        return self.page.locator(Selectors.RECEIPT).inner_html()

    def screenshot_robot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.page.locator(Selectors.ROBOT_PREVIEW_IMAGE).screenshot(path=str(path))
        return path

    def screenshot_page(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(path), full_page=True)
        return path

    def capture_evidence(self, path: Path) -> Path | None:
        """Captura de un pedido fallido; si el navegador tampoco responde, no tumba el lote."""
        try:
            return self.screenshot_page(path)
        except Exception:
            return None

    def order_another(self) -> None:
        self.page.click(Selectors.ORDER_ANOTHER)

    def reset(self) -> bool:
        """Vuelve a un formulario limpio después de un pedido fallido.

        Devuelve ``False`` si el sitio no cargó: el siguiente pedido lo intentará de nuevo y, si
        sigue caído, quedará como fallido con su propia evidencia, sin detener el lote.
        """
        try:
            self.open()
        except Exception:
            return False
        return True
