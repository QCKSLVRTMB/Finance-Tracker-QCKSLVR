"""Генерация примера книги Excel из sample_data.json."""

from pathlib import Path

from finance_tracker.storage.excel_io import export_workbook
from finance_tracker.storage.json_io import load_project

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    data = load_project(root / "data" / "sample_data.json")
    export_workbook(data, root / "sample.xlsx")
    print("Готово: sample.xlsx")
