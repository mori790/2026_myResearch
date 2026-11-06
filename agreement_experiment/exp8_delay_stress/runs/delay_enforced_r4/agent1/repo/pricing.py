"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Implements the committed decision PRICING_API (v1):
  get_item(sku)               -> {"sku", "name", "price" (float dollars), "category"} or None
  get_customer(customer_id)   -> {"id", "name", "discount" (fraction, e.g. 0.10), "region"} or None
  get_price(sku, customer_id) -> float dollars = price * (1 - discount), or None

Units (team coding standard):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Note on tax boundary (agreed in tax_api): tax.py takes integer cents and percent numbers.
Callers (invoice.py) convert at that boundary: cents = round(price * 100),
discount_pct = discount * 100.

The data files are in data_pricing/ next to this file:
  - catalog.csv   columns: sku,name,price_cents,category
  - customers.csv columns: id,name,discount_pct,region
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _load_catalog():
    items = {}
    path = os.path.join(_DATA_DIR, "catalog.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Stored in cents in the file; converted to dollars here.
                "price": int(row["price_cents"]) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers():
    customers = {}
    path = os.path.join(_DATA_DIR, "customers.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # Stored as whole percent in the file; converted to a fraction here.
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info {"sku", "name", "price" (dollars), "category"}, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info {"id", "name", "discount" (fraction), "region"}, or None if id is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def get_price(sku, customer_id):
    """Return the discounted unit price in dollars: price * (1 - discount).

    Returns None if either the sku or the customer id is unknown.
    """
    item = _ITEMS.get(sku)
    customer = _CUSTOMERS.get(customer_id)
    if item is None or customer is None:
        return None
    return item["price"] * (1 - customer["discount"])
