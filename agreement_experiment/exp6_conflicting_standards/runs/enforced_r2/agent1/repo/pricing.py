"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Public API (decision ``pricing_api``, committed v1):
  get_item(sku)                -> {"sku", "name", "price", "category"} or None
  get_customer(customer_id)    -> {"id", "name", "discount", "region"} or None

Conventions:
  - money amounts are floats in dollars (12.5 means $12.50)
  - percentages are fractions (10% is 0.10)
  - lookups that find nothing return None
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Stored in cents in catalog.csv; converted to dollars (float).
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
                # Stored as a percent (10) in customers.csv; converted to a fraction (0.10).
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(os.path.join(_DATA_DIR, "catalog.csv"))
_CUSTOMERS = _load_customers(os.path.join(_DATA_DIR, "customers.csv"))


def get_item(sku):
    """Return {sku, name, price (dollars), category} for sku, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return {id, name, discount (fraction), region} for customer_id, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
