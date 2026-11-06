"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Units (committed decisions money_percent_repr and PRICING_API_V2):
  - money is an integer number of cents (1250 = $12.50)
  - percents are percent numbers (10 = 10%), not fractions

Lookups return None when nothing is found (no KeyError is raised).

The data files are in data_pricing/ next to this file:
  catalog.csv    sku,name,price_cents,category
  customers.csv  id,name,discount_pct,region
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _parse_number(text):
    """Parse a percent value from the CSV: integer text gives int, otherwise float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items():
    items = {}
    path = os.path.join(_DATA_DIR, "catalog.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": int(row["price_cents"].strip()),
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
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info for sku as a new dict, or None if the sku is unknown.

    Result keys: sku (str), name (str), price_cents (int), category (str).
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for customer_id as a new dict, or None if unknown.

    Result keys: id (str), name (str), discount_pct (number, percent: 10 = 10%),
    region (str).
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
