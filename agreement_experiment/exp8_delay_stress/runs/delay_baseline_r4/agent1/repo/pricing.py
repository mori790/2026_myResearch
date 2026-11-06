"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Public API (agreed on the team's agreement log as topic "pricing_api"):

    get_item(sku: str) -> dict | None
        {"sku": str, "name": str, "price": float, "category": str}
        price is in dollars (1250 cents -> 12.5). None if sku is unknown.

    get_customer(customer_id: str) -> dict | None
        {"id": str, "name": str, "discount_rate": float, "region": str}
        discount_rate is a fraction (10% -> 0.10). None if id is unknown.

Conventions: money in float dollars, percentages as fractions, lookups return None
when nothing is found. SKUs and customer ids are case-sensitive strings.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path=_CATALOG_PATH):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Stored in cents in the CSV; convert to float dollars.
                "price": int(row["price_cents"]) / 100.0,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # Stored as a whole-number percent in the CSV; convert to a fraction.
                "discount_rate": float(row["discount_pct"]) / 100.0,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info for sku, or None if sku is unknown.

    Returns a fresh copy so callers cannot modify the cached catalog.
    """
    item = _ITEMS.get(sku)
    if item is None:
        return None
    return dict(item)


def get_customer(customer_id):
    """Return customer info for customer_id, or None if the id is unknown.

    Returns a fresh copy so callers cannot modify the cached customer data.
    """
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return None
    return dict(customer)
