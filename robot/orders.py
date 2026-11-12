"""Pedidos: descarga del CSV y conversión a objetos validados (lógica pura, sin navegador).

Una fila inválida es un **error de negocio**: no se reintenta ni detiene el lote. Se aparta con
su número de línea y el motivo, y los pedidos válidos siguen su curso. Los mensajes nombran la
columna que falló, nunca los valores de la fila (la dirección es un dato personal).
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

CATALOG: frozenset[str] = frozenset(str(n) for n in range(1, 7))


class InvalidOrderError(ValueError):
    """Fila del CSV que no se puede procesar (error de negocio: no se reintenta)."""


def _field(row: Mapping[str, str | None], column: str) -> str:
    value = row.get(column)
    if value is None:  # csv.DictReader rellena con None las filas cortas
        raise InvalidOrderError(f"falta la columna «{column}»")
    return value.strip()


@dataclass(frozen=True, slots=True)
class Order:
    number: int
    head: str
    body: str
    legs: str
    address: str

    @classmethod
    def from_row(cls, row: Mapping[str, str | None]) -> Order:
        raw_number = _field(row, "Order number")
        if not raw_number.isdigit() or int(raw_number) < 1:
            raise InvalidOrderError("número de pedido no numérico")
        order = cls(
            number=int(raw_number),
            head=_field(row, "Head"),
            body=_field(row, "Body"),
            legs=_field(row, "Legs"),
            address=_field(row, "Address"),
        )
        order.validate()
        return order

    def validate(self) -> None:
        if self.head not in CATALOG:
            raise InvalidOrderError(f"pedido {self.number}: cabeza fuera de catálogo (1 a 6)")
        if self.body not in CATALOG:
            raise InvalidOrderError(f"pedido {self.number}: cuerpo fuera de catálogo (1 a 6)")
        if not self.legs.isdigit():
            raise InvalidOrderError(f"pedido {self.number}: número de piernas inválido")
        if not self.address:
            raise InvalidOrderError(f"pedido {self.number}: dirección vacía")


@dataclass(frozen=True, slots=True)
class RejectedRow:
    """Fila apartada por error de negocio: línea del CSV (la 1 es el encabezado) y motivo."""

    line: int
    reason: str


@dataclass(slots=True)
class Batch:
    """Lote del día: pedidos listos para procesar y filas apartadas."""

    orders: list[Order] = field(default_factory=list)
    rejected: list[RejectedRow] = field(default_factory=list)


def parse_orders(rows: Iterable[Mapping[str, str | None]]) -> Batch:
    """Valida fila por fila: una fila mala se aparta y las demás siguen."""
    batch = Batch()
    for line, row in enumerate(rows, start=2):
        try:
            batch.orders.append(Order.from_row(row))
        except InvalidOrderError as error:
            batch.rejected.append(RejectedRow(line=line, reason=str(error)))
    return batch


def read_orders(path: Path) -> Batch:
    with path.open(newline="", encoding="utf-8") as handle:
        return parse_orders(csv.DictReader(handle))


def download_orders(url: str, target: Path) -> Batch:
    """Descarga el CSV del día (siempre sobrescribe) y lo convierte en un lote validado."""
    from RPA.HTTP import HTTP  # importación diferida: las pruebas no necesitan RPA Framework

    target.parent.mkdir(parents=True, exist_ok=True)
    HTTP().download(url=url, target_file=str(target), overwrite=True)
    return read_orders(target)
