"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Agreed API (pricing.api v1, pricing.money_and_percent_units v1):
  get_item(sku)                -> dict {sku, name, price, category} or None
  get_customer(customer_id)    -> dict {id, name, discount, region} or None
  list_skus()                  -> list[str]
  list_customer_ids()          -> list[str]

Units: money is float dollars (12.5 means $12.50); discount is a float fraction
(0.10 means 10%). The raw CSVs store price_cents and discount_pct as integers, so
they are converted on load. A lookup that finds nothing returns None.
This module does no tax and no invoice computation.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(f)]


def _load_items():
    items = {}
    for row in _read_rows(_CATALOG_PATH):
        sku = row["sku"]
        if not sku:
            continue
        if sku in items:
            raise ValueError(f"duplicate sku in catalog.csv: {sku!r}")
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            "price": round(int(row["price_cents"]) / 100, 2),  # cents -> dollars
            "category": row["category"],
        }
    return items


def _load_customers():
    customers = {}
    for row in _read_rows(_CUSTOMERS_PATH):
        cid = row["id"]
        if not cid:
            continue
        if cid in customers:
            raise ValueError(f"duplicate id in customers.csv: {cid!r}")
        customers[cid] = {
            "id": cid,
            "name": row["name"],
            "discount": int(row["discount_pct"]) / 100,  # percent -> fraction
            "region": row["region"],
        }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return a copy of the item record for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_skus():
    """Return all SKUs in catalog order."""
    return list(_ITEMS.keys())


def list_customer_ids():
    """Return all customer IDs in file order."""
    return list(_CUSTOMERS.keys())
