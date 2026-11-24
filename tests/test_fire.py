from datetime import date
from decimal import Decimal

from finance_tracker.services.fire import FireParams, plan_fire


def test_required_capital():
    p = FireParams(
        monthly_income=Decimal("43446"),
        annual_rate=Decimal("0.21"),
        contribution_share=Decimal("0.10"),
        current_invested=Decimal("468771.50"),
        retirement_date=date(2028, 11, 24),
        today=date(2026, 11, 25),
    )
    r = plan_fire(p)
    assert r.annual_target == Decimal("521352.00")
    assert r.required_capital == Decimal("2482628.57")
    assert r.days_left == 730
    assert 0 < r.progress < 1
    assert len(r.growth_no_contrib) == 3
