"""Конфигурация: имена листов Excel и значения по умолчанию."""

from decimal import Decimal

from finance_tracker.models.assets import AssetClass

# Имена листов (как в книге на скриншотах)
SHEET_BALANCE = "Активы и пассивы"
SHEET_INCOME = "Доходы в месяц"
SHEET_EXPENSE = "Расходы в месяц"
SHEET_FIRE = "FIRE"

# Целевая аллокация инвестируемой части портфеля (лист "Активы и пассивы", K:N)
DEFAULT_TARGETS: dict[AssetClass, Decimal] = {
    AssetClass.STOCKS: Decimal("0.90"),
    AssetClass.DERIVATIVES: Decimal("0.05"),
    AssetClass.CRYPTO: Decimal("0.05"),
}

# Классы, входящие в "инвестируемое ядро" портфеля
INVESTED_CLASSES: frozenset[AssetClass] = frozenset(
    {AssetClass.STOCKS, AssetClass.DERIVATIVES, AssetClass.CRYPTO}
)

# Соответствие подписей в Excel -> класс актива (для импорта)
RU_TO_ASSET_CLASS: dict[str, AssetClass] = {
    "акции": AssetClass.STOCKS,
    "фьючерсы": AssetClass.DERIVATIVES,
    "опционы": AssetClass.DERIVATIVES,
    "деривативы": AssetClass.DERIVATIVES,
    "криптовалюта": AssetClass.CRYPTO,
    "недвижимость": AssetClass.REAL_ESTATE,
    "долг": AssetClass.RECEIVABLES,
}
