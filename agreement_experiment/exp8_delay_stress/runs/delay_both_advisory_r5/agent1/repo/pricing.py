"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Interface (committed decision pricing_api v3):
    get_item(sku)                -> dict {sku, name, unit_price_cents, category}
                                    raises KeyError if sku is unknown
    get_customer(customer_id)    -> dict {id, name, discount_pct, region}
                                    raises KeyError if customer_id is unknown
    list_items()                 -> list of item dicts
    list_customers()             -> list of customer dicts

Conventions:
    - money is an integer number of cents (1250 means $12.50)
    - percentages are percent numbers (10 means 10 percent), never fractions
    - an unknown sku or customer_id raises KeyError

The data files are in data_pricing/ next to this file.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _parse_number(text):
    """Parse a percent number: int if it is written as a whole number, otherwise float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in {path}: {sku}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path}: {cid}")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(os.path.join(_DATA_DIR, "catalog.csv"))
_CUSTOMERS = _load_customers(os.path.join(_DATA_DIR, "customers.csv"))


def get_item(sku):
    """Return a copy of the item dict for sku. Raises KeyError if the sku is unknown."""
    try:
        return dict(_ITEMS[sku])
    except KeyError:
        raise KeyError(f"unknown sku: {sku!r}") from None


def get_customer(customer_id):
    """Return a copy of the customer dict for customer_id. Raises KeyError if unknown."""
    try:
        return dict(_CUSTOMERS[customer_id])
    except KeyError:
        raise KeyError(f"unknown customer id: {customer_id!r}") from None


def list_items():
    """Return a list of copies of all item dicts, in catalog order."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers():
    """Return a list of copies of all customer dicts, in file order."""
    return [dict(c) for c in _CUSTOMERS.values()]
