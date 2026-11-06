"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed everywhere in this module):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)                -> Item | None
  get_customer(customer_id)    -> Customer | None
  list_items()                 -> list[Item]     (catalog order)
  list_customers()             -> list[Customer] (file order)

  Item has:     sku (str), name (str), price (float, dollars),
                category (str)
  Customer has: id (str), name (str), discount (float, fraction),
                region (str)
"""

import csv
import os
from dataclasses import dataclass

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price: float      # dollars, e.g. 12.5 means $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float   # fraction, e.g. 0.10 means 10% off
    region: str


def _read_rows(path):
    """Yield stripped field dicts from a CSV file, skipping blank lines."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {k.strip(): (v or "").strip() for k, v in row.items() if k is not None}
            if not any(cleaned.values()):
                continue
            yield cleaned


def _load_items(path):
    items = {}
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku {sku!r} in {path}")
        try:
            cents = int(row["price_cents"])
        except ValueError:
            raise ValueError(f"bad price_cents {row['price_cents']!r} for sku {sku!r} in {path}")
        if cents < 0:
            raise ValueError(f"negative price for sku {sku!r} in {path}")
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=cents / 100,          # cents -> dollars
            category=row["category"],
        )
    return items


def _load_customers(path):
    customers = {}
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id {cid!r} in {path}")
        try:
            pct = float(row["discount_pct"])
        except ValueError:
            raise ValueError(f"bad discount_pct {row['discount_pct']!r} for customer {cid!r} in {path}")
        if not 0 <= pct <= 100:
            raise ValueError(f"discount_pct {pct} out of range for customer {cid!r} in {path}")
        customers[cid] = Customer(
            id=cid,
            name=row["name"],
            discount=pct / 100,         # percent -> fraction
            region=row["region"],
        )
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item with this SKU, or None if there is no such item."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def list_items():
    """Return all items in catalog order."""
    return list(_ITEMS.values())


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
