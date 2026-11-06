"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Units (committed in the shared decision log, MONEY_REPRESENTATION v2 and module_api v2):
  - All money is integer cents (USD).
  - Percentages are integer thousandths of a percent (10% = 10000).

Public API:

    get_item(sku: str) -> dict | None
        {"sku": str, "name": str, "category": str, "unit_price_cents": int}
        Returns None if the SKU is unknown.

    get_customer(customer_id: str) -> dict | None
        {"id": str, "name": str, "region": str, "discount_pm": int}
        Returns None if the customer is unknown.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_FILE = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_FILE = os.path.join(_DATA_DIR, "customers.csv")

__all__ = ["get_item", "get_customer"]


class PricingDataError(ValueError):
    """Raised when a pricing data file is malformed."""


def _read_rows(path: str, required: list) -> list:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise PricingDataError(f"{path}: file is empty")
        fieldnames = [f.strip() for f in reader.fieldnames]
        missing = [c for c in required if c not in fieldnames]
        if missing:
            raise PricingDataError(f"{path}: missing column(s) {missing}")
        rows = []
        for lineno, raw in enumerate(reader, start=2):
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            row["_where"] = f"{path}:{lineno}"
            rows.append(row)
        return rows


def _load_catalog() -> Dict[str, dict]:
    items: Dict[str, dict] = {}
    for row in _read_rows(_CATALOG_FILE, ["sku", "name", "price_cents", "category"]):
        where = row["_where"]
        sku = row["sku"]
        if not sku:
            raise PricingDataError(f"{where}: empty sku")
        if sku in items:
            raise PricingDataError(f"{where}: duplicate sku {sku!r}")
        try:
            price = int(row["price_cents"])
        except ValueError:
            raise PricingDataError(f"{where}: price_cents must be an integer") from None
        if price < 0:
            raise PricingDataError(f"{where}: price_cents must be non-negative")
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            "category": row["category"],
            "unit_price_cents": price,
        }
    return items


def _load_customers() -> Dict[str, dict]:
    customers: Dict[str, dict] = {}
    for row in _read_rows(_CUSTOMERS_FILE, ["id", "name", "discount_pct", "region"]):
        where = row["_where"]
        cid = row["id"]
        if not cid:
            raise PricingDataError(f"{where}: empty id")
        if cid in customers:
            raise PricingDataError(f"{where}: duplicate customer id {cid!r}")
        try:
            pct = int(row["discount_pct"])
        except ValueError:
            raise PricingDataError(f"{where}: discount_pct must be an integer percent") from None
        if not 0 <= pct <= 100:
            raise PricingDataError(f"{where}: discount_pct must be between 0 and 100")
        customers[cid] = {
            "id": cid,
            "name": row["name"],
            "region": row["region"],
            # CSV holds whole percents; the shared API uses thousandths of a percent.
            "discount_pm": pct * 1000,
        }
    return customers


_ITEMS: Dict[str, dict] = _load_catalog()
_CUSTOMERS: Dict[str, dict] = _load_customers()


def get_item(sku: str) -> Optional[dict]:
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id: str) -> Optional[dict]:
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
