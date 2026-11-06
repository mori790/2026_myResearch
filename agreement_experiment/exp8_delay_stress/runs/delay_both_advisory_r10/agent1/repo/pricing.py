"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed interface (pricing_api v2, shared decision log):
  get_item(sku: str) -> dict | None
      {"sku": str, "name": str, "price_cents": int, "category": str}
  get_customer(customer_id: str) -> dict | None
      {"id": str, "name": str, "discount_pct": number, "region": str}

Units (money-units, percent-units):
  - price_cents is an integer number of cents (1250 means $12.50).
  - discount_pct is a percent number (10 means 10%).

Lookups are exact-match and case-sensitive. An unknown SKU or customer id returns None.
Returned dicts are fresh copies, so callers cannot modify the cached data.
pricing.py does not apply discounts, tax, or rounding.
"""

import csv
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"

_items = None      # dict: sku -> record
_customers = None  # dict: customer id -> record


def _parse_percent(text):
    """Parse a percent number such as '10' or '8.25'. Integral values become int."""
    value = float(text.strip())
    if value.is_integer():
        return int(value)
    return value


def _load_items():
    items = {}
    with open(_CATALOG_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate SKU in catalog.csv: {sku!r}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": int(row["price_cents"].strip()),
                "category": row["category"].strip(),
            }
    return items


def _load_customers():
    customers = {}
    with open(_CUSTOMERS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": _parse_percent(row["discount_pct"]),
                "region": row["region"].strip().upper(),
            }
    return customers


def _get_items():
    global _items
    if _items is None:
        _items = _load_items()
    return _items


def _get_customers():
    global _customers
    if _customers is None:
        _customers = _load_customers()
    return _customers


def get_item(sku):
    """Return the item record for an exact SKU, or None if the SKU is unknown."""
    record = _get_items().get(sku)
    return dict(record) if record is not None else None


def get_customer(customer_id):
    """Return the customer record for an exact id, or None if the id is unknown."""
    record = _get_customers().get(customer_id)
    return dict(record) if record is not None else None
