"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed API (decision log topic: pricing_api v2):

    get_item(sku) -> dict | None
        {"sku": str, "name": str, "price": float, "price_cents": int,
         "category": str}
        price is in dollars (12.5 means $12.50); price_cents is the same
        amount in integer cents (1250).

    get_customer(customer_id) -> dict | None
        {"id": str, "name": str, "discount": float, "discount_pct": int,
         "region": str}
        discount is a fraction (0.10 means 10%); discount_pct is the same
        value as a percent number (10).

Lookups that find nothing return None. This module does no tax computation.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path=_CATALOG_PATH):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            price_cents = int(row["price_cents"])
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price": price_cents / 100,
                "price_cents": price_cents,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            discount_pct = int(row["discount_pct"])
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount": discount_pct / 100,
                "discount_pct": discount_pct,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return a copy of the item record for sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for customer_id, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
