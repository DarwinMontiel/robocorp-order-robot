from __future__ import annotations

from pathlib import Path

import pytest

from robot.orders import InvalidOrderError, Order, read_orders
from robot.receipts import receipt_path, screenshot_path

SAMPLE = Path(__file__).parent / "fixtures" / "orders.csv"


def test_reads_the_daily_csv_into_validated_orders() -> None:
    orders = read_orders(SAMPLE)
    assert len(orders) == 20
    assert orders[0] == Order(number=1, head="1", body="2", legs="3", address="Address 123")
    assert [o.number for o in orders] == list(range(1, 21))


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (
            {"Order number": "x", "Head": "1", "Body": "1", "Legs": "1", "Address": "A"},
            "fila inválida",
        ),
        ({"Order number": "1", "Head": "9", "Body": "1", "Legs": "1", "Address": "A"}, "cabeza"),
        ({"Order number": "1", "Head": "1", "Body": "0", "Legs": "1", "Address": "A"}, "cuerpo"),
        ({"Order number": "1", "Head": "1", "Body": "1", "Legs": "dos", "Address": "A"}, "piernas"),
        ({"Order number": "1", "Head": "1", "Body": "1", "Legs": "2", "Address": " "}, "dirección"),
        ({"Order number": "1", "Head": "1"}, "fila inválida"),
    ],
)
def test_invalid_rows_are_rejected_with_a_clear_reason(row: dict[str, str], message: str) -> None:
    with pytest.raises(InvalidOrderError, match=message):
        Order.from_row(row)


def test_output_paths_are_stable_per_order() -> None:
    assert receipt_path(7).as_posix() == "output/receipts/receipt_7.pdf"
    assert screenshot_path(7).as_posix() == "output/screenshots/robot_7.png"
