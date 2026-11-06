"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Implements the committed decision `pricing_api` (v1) in the shared agreement log:
- Money is integer cents (unit_price_cents), matching tax_api.
- Percentages are percent numbers (discount_pct 10 means 10%).
- A lookup that finds nothing returns None. No defaults are supplied here.

Public API:
- get_item(sku: str) -> dict {"sku", "name", "unit_price_cents" (int), "category"} or None
- get_customer(customer_id: str) -> dict {"id", "name", "discount_pct" (int, 0 if none), "region"} or None
"""

import csv
import os
from typing import Dict, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _read_rows(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(f)]


def _load_items() -> Dict[str, dict]:
    items: Dict[str, dict] = {}
    for row in _read_rows(_CATALOG_PATH):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in catalog.csv: {sku!r}")
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            "unit_price_cents": int(row["price_cents"]),
            "category": row["category"],
        }
    return items


def _load_customers() -> Dict[str, dict]:
    customers: Dict[str, dict] = {}
    for row in _read_rows(_CUSTOMERS_PATH):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
        customers[cid] = {
            "id": cid,
            "name": row["name"],
            "discount_pct": int(row["discount_pct"]),
            "region": row["region"],
        }
    return customers


_ITEMS: Dict[str, dict] = _load_items()
_CUSTOMERS: Dict[str, dict] = _load_customers()


def get_item(sku: str) -> Optional[dict]:
    """Return a copy of the item record for `sku`, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id: str) -> Optional[dict]:
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
