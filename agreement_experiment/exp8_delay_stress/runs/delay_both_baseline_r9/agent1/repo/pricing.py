"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku) -> dict | None
      {"sku": str, "name": str, "price": float (dollars), "category": str}
  get_customer(customer_id) -> dict | None
      {"id": str, "name": str, "discount": float (fraction, e.g. 0.10), "region": str}
  list_items() -> list[dict]        # all items, same shape as get_item
  list_customers() -> list[dict]    # all customers, same shape as get_customer

Returned dicts are fresh copies; mutating them does not affect the module's data.
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
                "price": int(row["price_cents"].strip()) / 100,
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
                # Source stores whole percent (10 means 10%); convert to fraction.
                "discount": float(row["discount_pct"].strip()) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for `sku`, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all items, sorted by SKU."""
    return [dict(_ITEMS[k]) for k in sorted(_ITEMS)]


def list_customers():
    """Return all customers, sorted by ID."""
    return [dict(_CUSTOMERS[k]) for k in sorted(_CUSTOMERS)]
