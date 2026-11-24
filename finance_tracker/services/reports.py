"""Текстовое оформление отчётов для консоли."""

from __future__ import annotations

from decimal import Decimal


def money(value: Decimal) -> str:
    return f"{value:,.2f}".replace(",", " ") + " ₽"


def pct(value: Decimal) -> str:
    return f"{value * 100:.2f}%"


def table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
              for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    sep = "-" * len(line)
    body = "\n".join(
        "  ".join(str(c).ljust(w) for c, w in zip(r, widths)) for r in rows
    )
    return f"{line}\n{sep}\n{body}"
