from decimal import Decimal

from finance_tracker.config import INVESTED_CLASSES
from finance_tracker.models.assets import Asset, AssetClass, BalanceSheet, Liability


def test_net_worth_and_invested():
    b = BalanceSheet(
        assets=[
            Asset("А", AssetClass.STOCKS, Decimal("100")),
            Asset("Б", AssetClass.CRYPTO, Decimal("50")),
            Asset("В", AssetClass.REAL_ESTATE, Decimal("1000")),
        ],
        liabilities=[Liability("L", Decimal("30"))],
    )
    assert b.total_assets() == Decimal("1150")
    assert b.net_worth() == Decimal("1120")
    assert b.invested_value(INVESTED_CLASSES) == Decimal("150")
