from __future__ import annotations

import pytest

from robot.retry import StepFailedError, retry_until


def test_returns_the_attempt_that_succeeded() -> None:
    clicks: list[int] = []
    results = iter([False, False, True])
    retried: list[int] = []

    attempt = retry_until(
        action=lambda: clicks.append(1),
        succeeded=lambda: next(results),
        attempts=5,
        description="enviar pedido",
        sleep=lambda _: None,
        on_retry=retried.append,
    )

    assert attempt == 3
    assert len(clicks) == 3
    assert retried == [1, 2]


def test_raises_after_exhausting_attempts() -> None:
    sleeps: list[float] = []
    with pytest.raises(StepFailedError, match="enviar pedido: sin éxito tras 3 intentos"):
        retry_until(
            lambda: None,
            lambda: False,
            attempts=3,
            description="enviar pedido",
            sleep=sleeps.append,
        )
    assert sleeps == [0.5, 0.5]  # no espera después del último intento
