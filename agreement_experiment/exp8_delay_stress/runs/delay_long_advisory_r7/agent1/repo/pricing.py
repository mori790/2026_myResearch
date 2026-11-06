"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Committed team conventions (see agree.py decisions pricing_*):
  * Money amounts are float dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API (committed as pricing_api):
  get_item(sku: str) -> dict | None
      {"sku": str, "name": str, "unit_price": float (dollars), "category": str}
  get_customer(customer_id: str) -> dict | None
      {"id": str, "name": str, "discount_rate": float (fraction), "region": str}
  list_items() -> list[dict]
  list_customers() -> list[dict]

The data files are in data_pricing/ next to this file and are loaded relative to
this module's location. Returned dicts are copies, so callers cannot change the
internal data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source is integer cents; convert to float dollars at the boundary.
                "unit_price": int(row["price_cents"]) / 100,
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
                # Source is whole percents; convert to a fraction (10 -> 0.10).
                "discount_rate": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(os.path.join(_DATA_DIR, "catalog.csv"))
_CUSTOMERS = _load_customers(os.path.join(_DATA_DIR, "customers.csv"))


def get_item(sku):
    """Return the item with this SKU as a dict, or None if it is not in the catalog."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with this id as a dict, or None if not found."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all catalog items as a list of dicts."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers():
    """Return all customers as a list of dicts."""
    return [dict(customer) for customer in _CUSTOMERS.values()]
