"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)          -> dict or None
      {"sku": str, "name": str, "price": float (dollars), "category": str}
  get_customer(cust_id)  -> dict or None
      {"id": str, "name": str, "discount": float (fraction), "region": str}
  list_skus()            -> list of str
  list_customer_ids()    -> list of str

Each call returns a fresh copy, so callers may modify the result safely.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_FILE = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_FILE = os.path.join(_DATA_DIR, "customers.csv")


def _load_items():
    items = {}
    with open(_CATALOG_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source stores integer cents; convert to float dollars.
                "price": round(int(row["price_cents"]) / 100, 2),
                "category": row["category"].strip(),
            }
    return items


def _load_customers():
    customers = {}
    with open(_CUSTOMERS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cust_id = row["id"].strip()
            customers[cust_id] = {
                "id": cust_id,
                "name": row["name"].strip(),
                # Source stores whole percentages (10 means 10%); convert to a fraction.
                "discount": round(int(row["discount_pct"]) / 100, 4),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info for `sku`, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(cust_id):
    """Return customer info for `cust_id`, or None if the customer is unknown."""
    customer = _CUSTOMERS.get(cust_id)
    return dict(customer) if customer is not None else None


def list_skus():
    """Return all known SKUs in catalog order."""
    return list(_ITEMS.keys())


def list_customer_ids():
    """Return all known customer IDs in file order."""
    return list(_CUSTOMERS.keys())
