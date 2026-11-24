"""Модели денежных потоков: доходы и расходы по категориям."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class FlowType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass
class FlowRecord:
    """Одна строка дохода/расхода (план и факт за месяц)."""

    name: str
    category: str
    planned: Decimal = Decimal("0")
    actual: Decimal = Decimal("0")
    flow_type: FlowType = FlowType.INCOME


@dataclass
class Cashflow:
    """Набор потоков (лист "Доходы в месяц" или "Расходы в месяц")."""

    flow_type: FlowType
    records: list[FlowRecord] = field(default_factory=list)

    def totals(self) -> tuple[Decimal, Decimal]:
        """(план, факт) по всем записям."""
        planned = sum((r.planned for r in self.records), Decimal("0"))
        actual = sum((r.actual for r in self.records), Decimal("0"))
        return planned, actual

    def by_category(self) -> dict[str, tuple[Decimal, Decimal]]:
        result: dict[str, tuple[Decimal, Decimal]] = {}
        for r in self.records:
            p, a = result.get(r.category, (Decimal("0"), Decimal("0")))
            result[r.category] = (p + r.planned, a + r.actual)
        return result
