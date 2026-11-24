"""Конфигурация: имена листов Excel, значения по умолчанию и каталог целей."""

from decimal import Decimal
from finance_tracker.models.assets import AssetClass

# Имена листов (как в книге на скриншотах)
SHEET_BALANCE = "Активы и пассивы"
SHEET_INCOME = "Доходы в месяц"
SHEET_EXPENSE = "Расходы в месяц"
SHEET_FIRE = "FIRE"

# Целевая аллокация инвестируемой части портфеля
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

# Каталог финансовых целей для конструктора дорожной карты
GOAL_CATALOG = {
    "A2": {"name": "Резерв 6 месяцев (Подушка)", "cost": 63000, "priority": 1, "type": "short"},
    "A4": {"name": "Досрочное погашение кредита (18,4%)", "cost": 181000, "priority": 2, "type": "short"},
    "A6": {"name": "Пополнение ИИС-3 (макс. вычет)", "cost": 400000, "priority": 3, "type": "short", "note": "Лимит для макс. налогового вычета"},
    "A7": {"name": "Пополнение ПДС (софинансирование)", "cost": 36000, "priority": 3, "type": "short", "note": "Макс. взнос для софинансирования 1:1"},
    "B13": {"name": "Капитал 1 000 000 ₽", "cost": 531229, "priority": 4, "type": "medium", "note": "Добить до 1 млн от текущих ~468 тыс."},
    "B1": {"name": "Первоначальный взнос (Ипотека)", "cost": 1500000, "priority": 5, "type": "medium"},
    "C1": {"name": "Пенсионный капитал (ПДС)", "cost": 540000, "priority": 6, "type": "long", "note": "36 000 ₽/год * 15 лет"},
}
