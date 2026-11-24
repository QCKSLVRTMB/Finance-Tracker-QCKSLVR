"""Сервис аллокации: рекомендуемые суммы и шаги ребалансировки (лист 1, K:N)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from finance_tracker.config import DEFAULT_TARGETS, INVESTED_CLASSES
from finance_tracker.models.assets import AssetClass, BalanceSheet


@dataclass
class RebalanceAction:
    asset_class: AssetClass
    current: Decimal
    target_share: Decimal
    recommended: Decimal
    delta: Decimal  # recommended - current (положительный = докупить)

    @property
    def action(self) -> str:
        if abs(self.delta) < Decimal("1"):
            return "—"
        return "купить" if self.delta > 0 else "продать"


def recommended_amounts(
    base: Decimal, targets: dict[AssetClass, Decimal] | None = None
) -> dict[AssetClass, Decimal]:
    """Распределить базу по целевым долям."""
    targets = targets or DEFAULT_TARGETS
    _validate(targets)
    return {cls: (base * share).quantize(Decimal("0.01")) for cls, share in targets.items()}


def rebalance(
    balance: BalanceSheet, targets: dict[AssetClass, Decimal] | None = None
) -> list[RebalanceAction]:
    """Сравнить текущую структуру инвест-ядра с целевой."""
    targets = targets or DEFAULT_TARGETS
    base = balance.invested_value(INVESTED_CLASSES)
    current = balance.value_by_class()
    rec = recommended_amounts(base, targets)

    actions: list[RebalanceAction] = []
    for cls in sorted(targets, key=str):
        cur = current.get(cls, Decimal("0"))
        recommended = rec[cls]
        actions.append(
            RebalanceAction(
                asset_class=cls,
                current=cur,
                target_share=targets[cls],
                recommended=recommended,
                delta=recommended - cur,
            )
        )
    return actions


def _validate(targets: dict[AssetClass, Decimal]) -> None:
    total = sum(targets.values(), Decimal("0"))
    if total != Decimal("1"):
        raise ValueError(f"Целевые доли должны давать 1.00, получено {total}")
