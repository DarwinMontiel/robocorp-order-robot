"""Reporte de turno: lo que un coordinador quiere leer al final del lote (lógica pura).

Se escribe en ``output/resumen.md`` y distingue los tres desenlaces posibles de un pedido:
entregado (con cuántos intentos necesitó), fallido por error de sistema (con su evidencia) y
apartado por error de negocio (con la línea del CSV y el motivo, sin volcar datos de la fila).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from robot.orders import RejectedRow
from robot.retry import StepFailedError


def describe_failure(error: Exception) -> str:
    """Motivo corto y sin datos del pedido: primera línea de los errores conocidos.

    Un error inesperado se resume solo con su tipo, porque su mensaje podría traer valores del
    formulario; para diagnosticarlo está la captura de pantalla en ``output/errores``.
    """
    if isinstance(error, (StepFailedError, PlaywrightTimeoutError)):
        return str(error).splitlines()[0]
    return f"{type(error).__name__}: error de sistema inesperado"


@dataclass(frozen=True, slots=True)
class Failure:
    reason: str
    evidence: Path | None = None


@dataclass(slots=True)
class ShiftReport:
    started_at: datetime
    delivered: dict[int, int] = field(default_factory=dict)  # pedido -> intento exitoso
    failed: dict[int, Failure] = field(default_factory=dict)
    rejected: list[RejectedRow] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.delivered) + len(self.failed) + len(self.rejected)

    @property
    def retries(self) -> int:
        return sum(attempt - 1 for attempt in self.delivered.values())

    @property
    def clean(self) -> bool:
        return not self.failed and not self.rejected

    def headline(self) -> str:
        return (
            f"{len(self.delivered)}/{self.total} pedidos entregados · "
            f"{len(self.failed)} fallidos · {len(self.rejected)} filas apartadas"
        )

    def render(self) -> str:
        lines = [
            "# Reporte de turno · Robot de pedidos",
            "",
            f"Inicio: {self.started_at:%Y-%m-%d %H:%M}",
            "",
            "| Indicador | Valor |",
            "|---|---:|",
            f"| Filas en el CSV | {self.total} |",
            f"| Pedidos entregados | {len(self.delivered)} |",
            f"| Reintentos usados | {self.retries} |",
            f"| Fallidos (error de sistema) | {len(self.failed)} |",
            f"| Apartados (error de negocio) | {len(self.rejected)} |",
        ]
        if self.failed:
            lines += ["", "## Fallidos: reprocesar", "", "| Pedido | Motivo | Evidencia |"]
            lines.append("|---:|---|---|")
            for number, failure in sorted(self.failed.items()):
                evidence = failure.evidence.as_posix() if failure.evidence else "sin captura"
                lines.append(f"| {number} | {failure.reason} | `{evidence}` |")
        if self.rejected:
            lines += ["", "## Apartados: corregir en el origen", "", "| Línea | Motivo |"]
            lines.append("|---:|---|")
            lines += [f"| {row.line} | {row.reason} |" for row in self.rejected]
        if self.clean:
            lines += ["", "Turno limpio: todos los pedidos tienen su recibo en `recibos.zip`."]
        return "\n".join(lines) + "\n"
