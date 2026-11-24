"""Цели: кратко-, средне- и долгосрочные (строки с вертикальной подписью на листах)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Horizon(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

    @property
    def ru_label(self) -> str:
        return {
            Horizon.SHORT: "Краткосрочные цели",
            Horizon.MEDIUM: "Среднесрочные цели",
            Horizon.LONG: "Долгосрочные цели",
        }[self]


@dataclass
class Goal:
    name: str
    horizon: Horizon
    planned: Decimal = Decimal("0")
    actual: Decimal = Decimal("0")
