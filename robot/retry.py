"""Reintento genérico para pasos frágiles de la interfaz (lógica pura y probada)."""

from __future__ import annotations

import time
from collections.abc import Callable


class StepFailedError(RuntimeError):
    """Un paso no tuvo éxito después de agotar los intentos (error de sistema)."""


def retry_until(
    action: Callable[[], None],
    succeeded: Callable[[], bool],
    attempts: int,
    description: str,
    wait_seconds: float = 0.5,
    sleep: Callable[[float], None] = time.sleep,
    on_retry: Callable[[int], None] | None = None,
) -> int:
    """Ejecuta ``action`` hasta que ``succeeded()`` sea verdadero. Devuelve el intento exitoso."""
    for attempt in range(1, attempts + 1):
        action()
        if succeeded():
            return attempt
        if attempt < attempts:
            if on_retry:
                on_retry(attempt)
            sleep(wait_seconds)
    raise StepFailedError(f"{description}: sin éxito tras {attempts} intentos")
