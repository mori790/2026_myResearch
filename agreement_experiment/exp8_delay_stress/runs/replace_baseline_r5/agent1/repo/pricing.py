"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category
  - customers.csv : id, name, discount_pct, region

Team conventions (applied at load time, so callers never see raw file units):
  - Money amounts are floats in dollars (1250 cents -> 12.5).
  - Percentages are fractions (discount_pct 10 -> 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)            -> Item | None
  get_customer(customer_id) -> Customer | None
  list_items()             -> list[Item]   (catalog order)
  list_customers()         -> list[Customer] (file order)
"""

import csv
import os
from dataclasses import dataclass
from functools import lru_cache

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.csv")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.csv")


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price: float  # dollars, e.g. 12.5 means $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float  # fraction, e.g. 0.10 means 10% off
    region: str


def _read_rows(path):
    # utf-8-sig tolerates a BOM if the file was saved by a spreadsheet tool.
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from every field and skip fully blank lines.
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k is not None}
            if any(row.values()):
                yield row


def _load_items():
    items = {}
    order = []
    for row in _read_rows(CATALOG_FILE):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate SKU in catalog.csv: {sku!r}")
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=int(row["price_cents"]) / 100.0,  # cents -> dollars
            category=row["category"],
        )
        order.append(sku)
    return items, order


def _load_customers():
    customers = {}
    order = []
    for row in _read_rows(CUSTOMERS_FILE):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
        customers[cid] = Customer(
            id=cid,
            name=row["name"],
            discount=int(row["discount_pct"]) / 100.0,  # percent -> fraction
            region=row["region"],
        )
        order.append(cid)
    return customers, order


@lru_cache(maxsize=1)
def _items_data():
    return _load_items()


@lru_cache(maxsize=1)
def _customers_data():
    return _load_customers()


def get_item(sku):
    """Return the Item with the given SKU, or None if no such item exists."""
    items, _ = _items_data()
    return items.get(sku)


def get_customer(customer_id):
    """Return the Customer with the given id, or None if no such customer exists."""
    customers, _ = _customers_data()
    return customers.get(customer_id)


def list_items():
    """Return all items in catalog order."""
    items, order = _items_data()
    return [items[sku] for sku in order]


def list_customers():
    """Return all customers in file order."""
    customers, order = _customers_data()
    return [customers[cid] for cid in order]
