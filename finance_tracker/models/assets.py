"""Модели баланса: активы, пассивы, балансовая ведомость."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class AssetClass(str, Enum):
    """Класс актива для аллокации."""

    STOCKS = "stocks"
    DERIVATIVES = "derivatives"
    CRYPTO = "crypto"
    REAL_ESTATE = "real_estate"
    RECEIVABLES = "receivables"
    OTHER = "other"

    @property
    def ru_label(self) -> str:
        return {
            AssetClass.STOCKS: "Акции",
            AssetClass.DERIVATIVES: "Деривативы",
            AssetClass.CRYPTO: "Криптовалюта",
            AssetClass.REAL_ESTATE: "Недвижимость",
            AssetClass.RECEIVABLES: "Дебиторская задолженность",
            AssetClass.OTHER: "Прочее",
        }[self]


@dataclass
class Asset:
    """Актив (строка раздела "Активы")."""

    name: str
    asset_class: AssetClass
    value: Decimal = Decimal("0")
    note: str = ""
    currency: str = "RUB"


@dataclass
class Liability:
    """Пассив (строка раздела "Пассивы")."""

    name: str
    value: Decimal = Decimal("0")
    note: str = ""
    sale_price: Optional[Decimal] = None


@dataclass
class BalanceSheet:
    """Балансовая ведомость (лист "Активы и пассивы")."""

    assets: list[Asset] = field(default_factory=list)
    liabilities: list[Liability] = field(default_factory=list)

    def total_assets(self) -> Decimal:
        return sum((a.value for a in self.assets), Decimal("0"))

    def total_liabilities(self) -> Decimal:
        return sum((l.value for l in self.liabilities), Decimal("0"))

    def net_worth(self) -> Decimal:
        """Капитал = активы - пассивы."""
        return self.total_assets() - self.total_liabilities()

    def value_by_class(self) -> dict[AssetClass, Decimal]:
        result: dict[AssetClass, Decimal] = {}
        for a in self.assets:
            result[a.asset_class] = result.get(a.asset_class, Decimal("0")) + a.value
        return result

    def invested_value(self, invested_classes: frozenset[AssetClass]) -> Decimal:
        """Стоимость инвестируемого ядра (акции + деривативы + крипта)."""
        by_class = self.value_by_class()
        return sum(
            (by_class.get(c, Decimal("0")) for c in invested_classes), Decimal("0")
        )
