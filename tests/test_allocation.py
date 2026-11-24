from decimal import Decimal

from finance_tracker.models.assets import Asset, AssetClass, BalanceSheet
from finance_tracker.services.allocation import rebalance, recommended_amounts


def test_recommended_sums_to_base():
    rec = recommended_amounts(Decimal("1000"))
    assert sum(rec.values()) == Decimal("1000.00")
    assert rec[AssetClass.STOCKS] == Decimal("900.00")


def test_rebalance_delta():
    b = BalanceSheet(assets=[
        Asset("А", AssetClass.STOCKS, Decimal("800")),
        Asset("К", AssetClass.CRYPTO, Decimal("100")),
        Asset("Д", AssetClass.DERIVATIVES, Decimal("100")),
    ])
    actions = {a.asset_class: a for a in rebalance(b)}
    assert actions[AssetClass.STOCKS].delta == Decimal("100.00")   # докупить
    assert actions[AssetClass.STOCKS].action == "купить"
