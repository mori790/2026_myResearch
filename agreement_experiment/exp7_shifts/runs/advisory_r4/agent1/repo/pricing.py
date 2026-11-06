"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed team decisions (see the shared decision log):
  - pricing.money: money amounts are floats in dollars (price_cents 1250 -> 12.5).
  - pricing.percent: percentages are fractions (discount_pct 10 -> 0.10).
  - pricing.lookup_miss: a lookup that finds nothing returns None.
  - pricing.api: get_item(sku), get_customer(customer_id), list_skus(), list_customer_ids().
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source stores integer cents; the team standard is float dollars.
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
                # Source stores whole-number percent; the team standard is a fraction.
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


# Loaded once at import; keys keep the file order (Python dicts preserve insertion order).
_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return {sku, name, price (dollars), category} for sku, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return {id, name, discount (fraction), region} for customer_id, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_skus():
    """Return the SKUs in catalog order."""
    return list(_ITEMS.keys())


def list_customer_ids():
    """Return the customer IDs in file order."""
    return list(_CUSTOMERS.keys())
