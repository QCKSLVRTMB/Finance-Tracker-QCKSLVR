"""Сериализация модели данных в JSON и обратно (Decimal -> строка)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from finance_tracker.models.assets import Asset, AssetClass, BalanceSheet, Liability
from finance_tracker.models.cashflow import Cashflow, FlowRecord, FlowType
from finance_tracker.models.goals import Goal, Horizon


def _d(v) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def load_project(path: str | Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return _build(raw)


def save_project(path: str | Path, raw: dict) -> None:
    Path(path).write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def _build(raw: dict) -> dict:
    balance = BalanceSheet(
        assets=[
            Asset(name=a["name"], asset_class=AssetClass(a["class"]),
                  value=_d(a["value"]), note=a.get("note", ""))
            for a in raw.get("assets", [])
        ],
        liabilities=[
            Liability(name=l["name"], value=_d(l["value"]), note=l.get("note", ""),
                      sale_price=_d(l["sale_price"]) if l.get("sale_price") is not None else None)
            for l in raw.get("liabilities", [])
        ],
    )
    income = Cashflow(FlowType.INCOME, [
        FlowRecord(name=r["name"], category=r.get("category", ""),
                   planned=_d(r.get("planned")), actual=_d(r.get("actual")),
                   flow_type=FlowType.INCOME)
        for r in raw.get("income", [])
    ])
    expense = Cashflow(FlowType.EXPENSE, [
        FlowRecord(name=r["name"], category=r.get("category", ""),
                   planned=_d(r.get("planned")), actual=_d(r.get("actual")),
                   flow_type=FlowType.EXPENSE)
        for r in raw.get("expense", [])
    ])
    goals = [
        Goal(name=g["name"], horizon=Horizon(g["horizon"]),
             planned=_d(g.get("planned")), actual=_d(g.get("actual")))
        for g in raw.get("goals", [])
    ]
    fire = raw.get("fire", {})
    return {"balance": balance, "income": income, "expense": expense,
            "goals": goals, "fire": fire}
