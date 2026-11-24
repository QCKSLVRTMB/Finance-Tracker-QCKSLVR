"""Агрегация доходов/расходов: план vs факт, разрывы по категориям."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from finance_tracker.models.cashflow import Cashflow


@dataclass
class CategorySummary:
    category: str
    planned: Decimal
    actual: Decimal

    @property
    def diff(self) -> Decimal:
        return self.actual - self.planned


def summarize(cf: Cashflow) -> list[CategorySummary]:
    return [
        CategorySummary(category=cat, planned=p, actual=a)
        for cat, (p, a) in sorted(cf.by_category().items())
    ]


def net_position(income: Cashflow, expense: Cashflow) -> Decimal:
    """Фактическая чистая позиция за период."""
    return income.totals()[1] - expense.totals()[1]
