"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed API (decision topic: pricing_api, v1):
    get_item(sku: str) -> dict | None
        keys: sku (str), name (str), price (float, dollars), category (str)
    get_customer(customer_id: str) -> dict | None
        keys: id (str), name (str), discount (float fraction, 0.10 = 10%), region (str or None)

Conventions:
    - Money is a float in dollars (1250 cents -> 12.5).
    - Percentages are fractions (10% -> 0.10).
    - A lookup that finds nothing returns None.
    - Lookups are exact string matches (no normalization).
    - This module computes no tax.
"""

import csv
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"

_items = None      # sku -> item dict
_customers = None  # customer id -> customer dict


def _load_items():
    items = {}
    with open(_CATALOG_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"]
            items[sku] = {
                "sku": sku,
                "name": row["name"],
                # Source column is integer cents; convert to float dollars.
                "price": int(row["price_cents"]) / 100,
                "category": row["category"],
            }
    return items


def _load_customers():
    customers = {}
    with open(_CUSTOMERS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"]
            region = row["region"] or None
            customers[cid] = {
                "id": cid,
                "name": row["name"],
                # Source column is an integer percent; convert to a fraction.
                "discount": int(row["discount_pct"]) / 100,
                "region": region,
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
    """Return a copy of the item record for `sku`, or None if the sku is unknown."""
    item = _get_items().get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _get_customers().get(customer_id)
    return dict(customer) if customer is not None else None
