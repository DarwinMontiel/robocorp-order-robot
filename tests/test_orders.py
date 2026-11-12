from __future__ import annotations

from pathlib import Path

import pytest

from robot.orders import InvalidOrderError, Order, RejectedRow, parse_orders, read_orders

FIXTURES = Path(__file__).parent / "fixtures"


def test_reads_the_daily_csv_into_validated_orders() -> None:
    batch = read_orders(FIXTURES / "orders.csv")
    assert len(batch.orders) == 20
    assert batch.rejected == []
    assert batch.orders[0] == Order(number=1, head="1", body="2", legs="3", address="Address 123")
    assert [o.number for o in batch.orders] == list(range(1, 21))


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (
            {"Order number": "x", "Head": "1", "Body": "1", "Legs": "1", "Address": "A"},
            "número de pedido no numérico",
        ),
        ({"Order number": "1", "Head": "9", "Body": "1", "Legs": "1", "Address": "A"}, "cabeza"),
        ({"Order number": "1", "Head": "1", "Body": "0", "Legs": "1", "Address": "A"}, "cuerpo"),
        ({"Order number": "1", "Head": "1", "Body": "1", "Legs": "dos", "Address": "A"}, "piernas"),
        ({"Order number": "1", "Head": "1", "Body": "1", "Legs": "2", "Address": " "}, "dirección"),
        ({"Order number": "1", "Head": "1"}, "falta la columna «Body»"),
        (
            {"Order number": "1", "Head": "1", "Body": "1", "Legs": "2", "Address": None},
            "falta la columna «Address»",
        ),
    ],
)
def test_invalid_rows_are_rejected_with_a_clear_reason(
    row: dict[str, str | None], message: str
) -> None:
    with pytest.raises(InvalidOrderError, match=message):
        Order.from_row(row)


def test_an_invalid_row_does_not_abort_the_batch() -> None:
    batch = read_orders(FIXTURES / "pedidos_mixtos.csv")

    assert [o.number for o in batch.orders] == [1, 3, 6]
    assert batch.rejected == [
        RejectedRow(line=3, reason="pedido 2: cabeza fuera de catálogo (1 a 6)"),
        RejectedRow(line=5, reason="número de pedido no numérico"),
        RejectedRow(line=6, reason="falta la columna «Legs»"),
    ]


def test_rejection_reasons_never_leak_row_values() -> None:
    secret = "Calle Ficticia 742"
    batch = parse_orders(
        [
            {"Order number": "1", "Head": "8", "Body": "1", "Legs": "2", "Address": secret},
            {"Order number": "abc", "Head": "1", "Body": "1", "Legs": "2", "Address": secret},
            {"Order number": "3", "Head": "1", "Body": "1", "Legs": "x", "Address": secret},
        ]
    )
    reasons = " ".join(row.reason for row in batch.rejected)
    assert len(batch.rejected) == 3
    assert secret not in reasons
    assert "abc" not in reasons
