"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Shared API (committed decisions: money_unit v2, percent_unit v1, lookup_miss v1, pricing_api v2):

    get_item(sku)          -> {"sku", "name", "unit_price", "category"} or None
    get_customer(cust_id)  -> {"id", "name", "discount_rate", "region"} or None

- unit_price is decimal.Decimal dollars (Decimal("12.50") means $12.50).
  The catalog stores cents; the conversion is exact (no float involved).
- discount_rate is a Decimal fraction (Decimal("0.10") means 10% off).
  The percentage in customers.csv is converted exactly.
- A lookup that finds nothing returns None (no exception).
"""

import csv
import os
from decimal import Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")

_items = None      # sku -> item dict
_customers = None  # customer id -> customer dict


def _load_items():
    items = {}
    path = os.path.join(_DATA_DIR, "catalog.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate SKU in catalog.csv: {sku!r}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # cents -> dollars, exact: 1250 -> Decimal("12.50")
                "unit_price": Decimal(row["price_cents"].strip()).scaleb(-2),
                "category": row["category"].strip(),
            }
    return items


def _load_customers():
    customers = {}
    path = os.path.join(_DATA_DIR, "customers.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # percent -> fraction, exact: 10 -> Decimal("0.10")
                "discount_rate": Decimal(row["discount_pct"].strip()).scaleb(-2),
                "region": row["region"].strip(),
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
    """Return a copy of the item record for `sku`, or None if the SKU is unknown."""
    if sku is None:
        return None
    record = _get_items().get(str(sku).strip())
    return dict(record) if record is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    if customer_id is None:
        return None
    record = _get_customers().get(str(customer_id).strip())
    return dict(record) if record is not None else None
