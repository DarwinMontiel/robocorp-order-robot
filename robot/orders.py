"""Pedidos: descarga del CSV y conversión a objetos validados (lógica pura, sin navegador)."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path


class InvalidOrderError(ValueError):
    """Fila del CSV que no se puede procesar (error de negocio: no se reintenta)."""


@dataclass(frozen=True, slots=True)
class Order:
    number: int
    head: str
    body: str
    legs: str
    address: str

    @classmethod
    def from_row(cls, row: Mapping[str, str]) -> Order:
        try:
            order = cls(
                number=int(row["Order number"]),
                head=row["Head"].strip(),
                body=row["Body"].strip(),
                legs=row["Legs"].strip(),
                address=row["Address"].strip(),
            )
        except (KeyError, ValueError) as error:
            raise InvalidOrderError(f"fila inválida {dict(row)}: {error}") from error
        order.validate()
        return order

    def validate(self) -> None:
        if self.head not in {str(n) for n in range(1, 7)}:
            raise InvalidOrderError(f"pedido {self.number}: cabeza fuera de catálogo ({self.head})")
        if self.body not in {str(n) for n in range(1, 7)}:
            raise InvalidOrderError(f"pedido {self.number}: cuerpo fuera de catálogo ({self.body})")
        if not self.legs.isdigit():
            raise InvalidOrderError(
                f"pedido {self.number}: número de piernas inválido ({self.legs})"
            )
        if not self.address:
            raise InvalidOrderError(f"pedido {self.number}: dirección vacía")


def parse_orders(rows: Iterable[Mapping[str, str]]) -> Iterator[Order]:
    for row in rows:
        yield Order.from_row(row)


def read_orders(path: Path) -> list[Order]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(parse_orders(csv.DictReader(handle)))


def download_orders(url: str, target: Path) -> list[Order]:
    """Descarga el CSV del día (siempre sobrescribe) y lo convierte en pedidos."""
    from RPA.HTTP import HTTP  # importación diferida: las pruebas no necesitan RPA Framework

    target.parent.mkdir(parents=True, exist_ok=True)
    HTTP().download(url=url, target_file=str(target), overwrite=True)
    return read_orders(target)
