"""Импорт/экспорт книги Excel (openpyxl).

Импорт листа "Активы и пассивы" повторяет макет со скриншота:
  A=наименование актива, B=комментарий/тип, C=стоимость;
  D=наименование пассива, E=комментарий, F=стоимость, G=цена продажи.
Листы доходов/расходов импортируются в нормализованном виде
(Категория | Название | План | Факт) — экспорт пишет именно такой макет.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from finance_tracker.config import (
    RU_TO_ASSET_CLASS,
    SHEET_BALANCE,
    SHEET_EXPENSE,
    SHEET_FIRE,
    SHEET_INCOME,
)
from finance_tracker.models.assets import Asset, AssetClass, BalanceSheet, Liability
from finance_tracker.models.cashflow import Cashflow, FlowRecord, FlowType


def _dec(value) -> Decimal | None:
    if value is None or isinstance(value, str):
        return None
    return Decimal(str(value))


# ----------------------------- IMPORT -----------------------------

def load_balance_sheet(ws: Worksheet) -> BalanceSheet:
    balance = BalanceSheet()
    mode = None
    for row in ws.iter_rows(values_only=True):
        a, b, c = (row + (None, None, None))[:3]
        d, e, f, g = (row + (None, None, None, None))[:7]
        text_a = str(a).strip() if a else ""
        text_d = str(d).strip() if d else ""

        if "Наименование актива" in text_a:
            mode = "assets"
            continue
        if "Наименование пассива" in text_d:
            mode = "liabilities"
            continue
        if text_a.startswith("Всего") or text_d == "Итого":
            continue

        if mode == "assets" and text_a and isinstance(c, (int, float)):
            cls = RU_TO_ASSET_CLASS.get(str(b or "").strip().lower(), AssetClass.OTHER)
            balance.assets.append(Asset(name=text_a, asset_class=cls,
                                        value=_dec(c) or Decimal("0"),
                                        note=str(b or "")))
        if mode == "liabilities" and text_d and isinstance(f, (int, float)):
            balance.liabilities.append(Liability(name=text_d, value=_dec(f) or Decimal("0"),
                                                 note=str(e or ""), sale_price=_dec(g)))
    return balance


def load_cashflow(ws: Worksheet, flow_type: FlowType) -> Cashflow:
    """Ожидает нормализованные колонки: Категория | Название | План | Факт."""
    records: list[FlowRecord] = []
    started = False
    for row in ws.iter_rows(values_only=True):
        cells = list(row) + [None] * 4
        b, c, d, e = cells[1:5]
        if str(c or "").strip() == "Название":
            started = True
            continue
        if started and c and isinstance(d, (int, float)):
            records.append(FlowRecord(name=str(c), category=str(b or ""),
                                      planned=_dec(d) or Decimal("0"),
                                      actual=_dec(e) or Decimal("0"),
                                      flow_type=flow_type))
    return Cashflow(flow_type=flow_type, records=records)


def load_workbook_data(path: str | Path) -> dict:
    wb = load_workbook(path, data_only=True)
    out: dict = {}
    if SHEET_BALANCE in wb.sheetnames:
        out["balance"] = load_balance_sheet(wb[SHEET_BALANCE])
    if SHEET_INCOME in wb.sheetnames:
        out["income"] = load_cashflow(wb[SHEET_INCOME], FlowType.INCOME)
    if SHEET_EXPENSE in wb.sheetnames:
        out["expense"] = load_cashflow(wb[SHEET_EXPENSE], FlowType.EXPENSE)
    return out


# ----------------------------- EXPORT -----------------------------

def export_workbook(data: dict, path: str | Path) -> None:
    """Собрать книгу Excel из модели данных (для бэкапа/переноса)."""
    wb = Workbook()
    _write_balance(wb.active, data["balance"])
    _write_cashflow(wb.create_sheet(SHEET_INCOME), data["income"])
    _write_cashflow(wb.create_sheet(SHEET_EXPENSE), data["expense"])
    _write_fire(wb.create_sheet(SHEET_FIRE), data.get("fire", {}))
    wb.save(path)


def _write_balance(ws: Worksheet, balance: BalanceSheet) -> None:
    ws.append(["Активы"])
    ws.append(["Наименование актива", "Комментарий", "Стоимость"])
    for a in balance.assets:
        ws.append([a.name, a.asset_class.ru_label, float(a.value)])
    ws.append(["Всего:", "", float(balance.total_assets())])
    ws.append([])
    ws.append(["Пассивы"])
    ws.append(["Наименование пассива", "Комментарий", "Стоимость", "Цена продажи"])
    for l in balance.liabilities:
        ws.append([l.name, l.note, float(l.value),
                   float(l.sale_price) if l.sale_price else None])
    ws.append(["Итого", "", float(balance.total_liabilities())])


def _write_cashflow(ws: Worksheet, cf: Cashflow) -> None:
    ws.append(["Категория", "Название", "План", "Факт"])
    for r in cf.records:
        ws.append([r.category, r.name, float(r.planned), float(r.actual)])
    p, a = cf.totals()
    ws.append(["", "Всего:", float(p), float(a)])


def _write_fire(ws: Worksheet, fire: dict) -> None:
    ws.append(["Параметр", "Значение"])
    for k, v in fire.items():
        ws.append([k, v])
