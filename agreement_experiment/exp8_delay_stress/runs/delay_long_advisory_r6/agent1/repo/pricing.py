"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed interface (decision `pricing_api`, v1):
    get_item(sku)                -> dict {sku, name, price, category} or None
    get_customer(customer_id)    -> dict {id, name, discount, region} or None

Team conventions:
    * money amounts are floats in dollars (12.5 means $12.50)
    * percentages are fractions (10% is 0.10)
    * a lookup that finds nothing returns None

The data files store prices in integer cents and discounts in whole percents;
they are converted at load time.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _read_rows(path):
    """Read a CSV file into a list of dicts, with stripped keys and values."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({k.strip(): (v or "").strip() for k, v in row.items() if k is not None})
    return rows


def _load_items():
    items = {}
    for row in _read_rows(_CATALOG_PATH):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in catalog.csv: {sku!r}")
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            # catalog stores integer cents; convert to float dollars.
            "price": int(row["price_cents"]) / 100,
            "category": row["category"],
        }
    return items


def _load_customers():
    customers = {}
    for row in _read_rows(_CUSTOMERS_PATH):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate id in customers.csv: {cid!r}")
        customers[cid] = {
            "id": cid,
            "name": row["name"],
            # customers store whole-number percents; convert to a fraction.
            "discount": int(row["discount_pct"]) / 100,
            "region": row["region"],
        }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info for `sku` as a dict, or None if the SKU is unknown.

    Returns a fresh copy, so callers cannot modify the loaded data.
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id` as a dict, or None if unknown.

    Returns a fresh copy, so callers cannot modify the loaded data.
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
