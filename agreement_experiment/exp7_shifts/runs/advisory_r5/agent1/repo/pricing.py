"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed API (decision log topic: pricing_api, v1):
  Money amounts are floats in dollars (12.5 means $12.50).
  Percentages are fractions (10% is 0.10).
  Lookups that find nothing return None.

  get_item(sku)            -> {"sku", "name", "price", "category"} or None
  get_customer(cust_id)    -> {"id", "name", "discount", "region"} or None
  list_items()             -> list of item dicts (same shape as get_item)
  list_customers()         -> list of customer dicts (same shape as get_customer)

This module returns base prices and the customer's discount fraction only.
It does not apply the discount and does not round; invoice.py does that.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _read_rows(path):
    """Read a CSV file into a list of dicts with whitespace stripped from keys and values."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for raw in reader:
            rows.append({(k or "").strip(): (v or "").strip() for k, v in raw.items()})
        return rows


def _load_items():
    items = {}
    for row in _read_rows(_CATALOG_PATH):
        sku = row["sku"]
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            # catalog stores integer cents; the team standard is float dollars
            "price": int(row["price_cents"]) / 100,
            "category": row["category"],
        }
    return items


def _load_customers():
    customers = {}
    for row in _read_rows(_CUSTOMERS_PATH):
        cust_id = row["id"]
        customers[cust_id] = {
            "id": cust_id,
            "name": row["name"],
            # catalog stores whole percentages; the team standard is fractions
            "discount": int(row["discount_pct"]) / 100,
            "region": row["region"],
        }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return a copy of the item dict for sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer dict for customer_id, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return copies of all item dicts, in catalog order."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers():
    """Return copies of all customer dicts, in file order."""
    return [dict(customer) for customer in _CUSTOMERS.values()]
