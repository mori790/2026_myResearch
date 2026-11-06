"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Shared interface (committed decision: pricing_interface v1):
  get_item(sku)                -> dict {sku: str, name: str, price: float (dollars),
                                        category: str}, or None if the SKU is unknown
  get_customer(customer_id)    -> dict {id: str, name: str, discount: float (fraction, 0.10 = 10%),
                                        region: str (e.g. "TX")}, or None if unknown

Conventions: money is float dollars, percentages are fractions, a lookup miss returns None.
This module contains no tax rules.
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
                # Source stores integer cents; convert to float dollars.
                "price": int(row["price_cents"]) / 100,
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
                # Source stores integer percent; convert to fraction.
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for customer_id, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
