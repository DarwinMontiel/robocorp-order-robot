"""Page Object del formulario de pedidos: toda interacción con el navegador vive aquí."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from robot.config import ORDER_URL, SUBMIT_ATTEMPTS, Selectors
from robot.orders import Order
from robot.retry import retry_until

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import Page


class OrderPage:
    def __init__(self, page: Page) -> None:
        self.page = page

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
            action=lambda: self.page.click(Selectors.ORDER),
            succeeded=lambda: self.page.is_visible(Selectors.RECEIPT),
            attempts=SUBMIT_ATTEMPTS,
            description="enviar pedido",
            on_retry=on_retry,
        )

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

    def order_another(self) -> None:
        self.page.click(Selectors.ORDER_ANOTHER)

    def reset(self) -> None:
        """Vuelve a un formulario limpio después de un pedido fallido."""
        self.open()
