"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
Data files live in data_pricing/ next to this file (catalog.csv, customers.csv).

Public API (see agreement topic "pricing_api"):
    get_item(sku)             -> dict | None
        keys: "sku" (str), "name" (str), "price" (float, dollars), "category" (str),
              "price_cents" (int, same price in integer cents)
    get_customer(customer_id) -> dict | None
        keys: "id" (str), "name" (str), "discount" (float fraction, 0.10 = 10%),
              "discount_pct" (int-valued percent, 10 = 10%), "region" (str, US state code)

The "price_cents" and "discount_pct" keys are convenience duplicates for callers
(e.g. tax.py) that work in integer cents and percent numbers. "price" and
"discount" are the canonical team-standard fields.

Conventions: money is float dollars (12.5 == $12.50); percentages are
fractions; a lookup that finds nothing returns None. Keys are case-sensitive.
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
            cents = int(row["price_cents"].strip())
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # price_cents is an integer count of cents; convert to dollars.
                "price": cents / 100.0,
                "price_cents": cents,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            pct = int(row["discount_pct"].strip())
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # discount is the fraction form (10% -> 0.10).
                "discount": pct / 100.0,
                "discount_pct": pct,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return the item with the given SKU as a dict, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with the given id as a dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
