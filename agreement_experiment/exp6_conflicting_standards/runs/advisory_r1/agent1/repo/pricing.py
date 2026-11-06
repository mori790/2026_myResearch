"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Committed API (agreement log: pricing_api v1, money_unit v3, percent_unit v1,
missing_lookup_signal v1):

    get_item(sku: str) -> dict | None
        {"sku": str, "name": str, "unit_price": float (dollars), "category": str}

    get_customer(customer_id: str) -> dict | None
        {"id": str, "name": str, "discount_rate": float (fraction, 0.10 = 10%),
         "region": str (e.g. "TX")}

Conventions:
    * Money amounts are floats in dollars (12.5 means $12.50).
    * Percentages are fractions (10% is 0.10).
    * A lookup that finds nothing returns None.

pricing does not compute tax or line totals.

The data files are in data_pricing/ next to this file.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # The CSV stores cents as an integer; convert to float dollars.
                "unit_price": int(row["price_cents"].strip()) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # The CSV stores percentages as whole numbers; convert to a fraction.
                "discount_rate": float(row["discount_pct"].strip()) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for `sku`, or None if the SKU is unknown.

    Returns a fresh copy so callers cannot modify the internal catalog.
    """
    item = _ITEMS.get(sku)
    if item is None:
        return None
    return dict(item)


def get_customer(customer_id):
    """Return customer info for `customer_id`, or None if unknown.

    Returns a fresh copy so callers cannot modify the internal customer data.
    """
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return None
    return dict(customer)
