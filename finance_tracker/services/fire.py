"""FIRE-планировщик: лист 4 (требуемый капитал, прогресс, таблицы роста)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

Q2 = Decimal("0.01")


@dataclass
class FireParams:
    monthly_income: Decimal          # основной доход за месяц
    annual_rate: Decimal             # ставка ЦБ / ожидаемая доходность, напр. 0.21
    contribution_share: Decimal      # доля дохода на пополнение, напр. 0.10
    current_invested: Decimal        # уже инвестировано
    retirement_date: date
    today: date = field(default_factory=date.today)


@dataclass
class YearRow:
    year: int
    start: Decimal
    end: Decimal


@dataclass
class FireResult:
    annual_target: Decimal           # нужные дивиденды в год
    required_capital: Decimal        # требуемые вложения
    monthly_contribution: Decimal
    yearly_contribution: Decimal
    days_left: int
    months_left: Decimal
    progress: Decimal                # доля от требуемого капитала
    contributions_to_date: Decimal
    shortfall: Decimal               # нехватка к требуемой сумме
    daily_topup: Decimal             # сколько докидывать в день
    required_monthly_income: Decimal # какой доход нужен при текущей доле пополнения
    growth_no_contrib: list[YearRow] = field(default_factory=list)
    growth_with_contrib: list[YearRow] = field(default_factory=list)


def plan_fire(p: FireParams) -> FireResult:
    if p.annual_rate <= 0:
        raise ValueError("Годовая ставка должна быть > 0")

    annual_target = (p.monthly_income * 12).quantize(Q2)
    required_capital = (annual_target / p.annual_rate).quantize(Q2)
    monthly_contribution = (p.monthly_income * p.contribution_share).quantize(Q2)

    days_left = max((p.retirement_date - p.today).days, 0)
    months_left = (Decimal(days_left) / Decimal("30.44")).quantize(Decimal("0.01"))
    progress = (p.current_invested / required_capital).quantize(Decimal("0.0001"))

    contributions_to_date = (monthly_contribution * months_left).quantize(Q2)
    shortfall = (required_capital - p.current_invested - contributions_to_date).quantize(Q2)

    daily_topup = (shortfall / Decimal(days_left)).quantize(Q2) if days_left else Q2
    req_income = (
        (shortfall / months_left / p.contribution_share).quantize(Q2)
        if months_left > 0
        else Q2
    )

    years = _years_to_retirement(p)
    return FireResult(
        annual_target=annual_target,
        required_capital=required_capital,
        monthly_contribution=monthly_contribution,
        yearly_contribution=(monthly_contribution * 12).quantize(Q2),
        days_left=days_left,
        months_left=months_left,
        progress=progress,
        contributions_to_date=contributions_to_date,
        shortfall=max(shortfall, Decimal("0")),
        daily_topup=daily_topup,
        required_monthly_income=req_income,
        growth_no_contrib=_project_growth(p.current_invested, p.annual_rate, Decimal("0"), years),
        growth_with_contrib=_project_growth(
            p.current_invested, p.annual_rate, monthly_contribution, years
        ),
    )


def _years_to_retirement(p: FireParams) -> int:
    return max((p.retirement_date.year - p.today.year) + 1, 1)


def _project_growth(
    start: Decimal, annual_rate: Decimal, monthly_contrib: Decimal,
    years: int, start_year: int,
) -> list[YearRow]:
    rows: list[YearRow] = []
    balance = start
    monthly_rate = (Decimal(1) + annual_rate) ** (Decimal(1) / Decimal(12)) - Decimal(1)
    for i in range(years):
        begin = balance
        for _ in range(12):
            balance = balance * (Decimal(1) + monthly_rate) + monthly_contrib
        rows.append(YearRow(year=start_year + i, start=begin.quantize(Q2), end=balance.quantize(Q2)))
    return rows
