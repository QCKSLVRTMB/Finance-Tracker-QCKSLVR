"""CLI: python main.py <команда>."""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path

from finance_tracker import __version__
from finance_tracker.config import DEFAULT_TARGETS
from finance_tracker.services.allocation import rebalance
from finance_tracker.services.cashflow import net_position, summarize
from finance_tracker.services.fire import FireParams, plan_fire
from finance_tracker.services.reports import money, pct, table
from finance_tracker.storage.excel_io import export_workbook, load_workbook_data
from finance_tracker.storage.json_io import load_project

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load(args) -> dict:
    path = Path(args.file)
    if path.suffix == ".xlsx":
        raw = load_workbook_data(path)
        raw.setdefault("fire", {})
        return raw
    return load_project(path)


def cmd_balance(args) -> None:
    b = _load(args)["balance"]
    print(f"Активы:      {money(b.total_assets())}")
    print(f"Пассивы:     {money(b.total_liabilities())}")
    print(f"Капитал:     {money(b.net_worth())}")


def cmd_allocation(args) -> None:
    b = _load(args)["balance"]
    actions = rebalance(b, DEFAULT_TARGETS)
    rows = [
        [a.asset_class.ru_label, pct(a.target_share), money(a.current),
         money(a.recommended), money(a.delta), a.action]
        for a in actions
    ]
    print(table(["Класс", "Цель", "Текущ.", "Реком.", "Δ", "Действие"], rows))


def cmd_fire(args) -> None:
    data = _load(args)
    fire = data["fire"]
    balance = data.get("balance")
    current = fire.get("current_invested")
    if current is None and balance is not None:
        from finance_tracker.config import INVESTED_CLASSES
        current = str(balance.invested_value(INVESTED_CLASSES))
    params = FireParams(
        monthly_income=Decimal(str(fire["monthly_income"])),
        annual_rate=Decimal(str(fire["annual_rate"])),
        contribution_share=Decimal(str(fire["contribution_share"])),
        current_invested=Decimal(str(current)),
        retirement_date=__import__("datetime").date.fromisoformat(fire["retirement_date"]),
    )
    r = plan_fire(params)
    print(f"Нужно дивидендов в год: {money(r.annual_target)}")
    print(f"Требуемый капитал:      {money(r.required_capital)}")
    print(f"Уже инвестировано:      {money(params.current_invested)} "
          f"({pct(r.progress)} от цели)")
    print(f"До пенсии: {r.days_left} дн. | нехватка: {money(r.shortfall)}")
    print(f"Нужно докидывать: {money(r.daily_topup)} в день")
    print("\nРост без пополнений:")
    print(table(["Год", "Начало", "Конец"],
                [[str(y.year), money(y.start), money(y.end)] for y in r.growth_no_contrib]))


def cmd_cashflow(args) -> None:
    data = _load(args)
    for key, title in (("income", "Доходы"), ("expense", "Расходы")):
        cf = data.get(key)
        if not cf:
            continue
        print(f"\n== {title} ==")
        print(table(["Категория", "План", "Факт", "Δ"],
                    [[s.category, money(s.planned), money(s.actual), money(s.diff)]
                     for s in summarize(cf)]))
    if "income" in data and "expense" in data:
        print(f"\nЧистая позиция (факт): {money(net_position(data['income'], data['expense']))}")


def cmd_export_xlsx(args) -> None:
    raw = load_project(DATA_DIR / "sample_data.json")
    export_workbook(raw, args.out)
    print(f"Книга сохранена: {args.out}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="finance-tracker", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_file(sp):
        sp.add_argument("--file", default=str(DATA_DIR / "sample_data.json"),
                        help="JSON или XLSX с данными")

    for cmd, fn, help_text in [
        ("balance", cmd_balance, "Баланс активов и пассивов"),
        ("allocation", cmd_allocation, "Аллокация и ребалансировка портфеля"),
        ("fire", cmd_fire, "Пенсионный (FIRE) план"),
        ("cashflow", cmd_cashflow, "Доходы/расходы план-факт"),
    ]:
        sp = sub.add_parser(cmd, help=help_text)
        add_file(sp)
        sp.set_defaults(func=fn)

    sp = sub.add_parser("export-xlsx", help="Собрать пример книги Excel")
    sp.add_argument("--out", default="sample.xlsx")
    sp.set_defaults(func=cmd_export_xlsx)

    args = parser.parse_args(argv)
    args.func(args)
