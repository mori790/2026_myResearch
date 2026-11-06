"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (decision pricing_api v1, committed):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)             -> Item or None
  get_customer(customer_id) -> Customer or None
  list_items()              -> list[Item]     (catalog order)
  list_customers()          -> list[Customer] (file order)

Item fields:     sku (str), name (str), price (float, dollars), category (str)
Customer fields: id (str), name (str), discount (float, fraction), region (str)
"""

import csv
import os
from dataclasses import dataclass
from functools import lru_cache

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
    discount: float   # fraction, e.g. 0.10 means 10%
    region: str


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield {(k or "").strip(): (v or "").strip() for k, v in row.items()}


@lru_cache(maxsize=None)
def _items():
    """Load catalog.csv once. Returns (tuple of Item, dict sku -> Item)."""
    items = []
    by_sku = {}
    for row in _read_rows(_CATALOG_PATH):
        # Source stores price as integer cents; convert to dollars.
        item = Item(
            sku=row["sku"],
            name=row["name"],
            price=round(int(row["price_cents"]) / 100, 2),
            category=row["category"],
        )
        if item.sku in by_sku:
            raise ValueError(f"duplicate SKU in catalog.csv: {item.sku!r}")
        by_sku[item.sku] = item
        items.append(item)
    return tuple(items), by_sku


@lru_cache(maxsize=None)
def _customers():
    """Load customers.csv once. Returns (tuple of Customer, dict id -> Customer)."""
    customers = []
    by_id = {}
    for row in _read_rows(_CUSTOMERS_PATH):
        # Source stores discount as a whole percent (10 means 10%); convert to a fraction.
        customer = Customer(
            id=row["id"],
            name=row["name"],
            discount=float(row["discount_pct"]) / 100,
            region=row["region"],
        )
        if customer.id in by_id:
            raise ValueError(f"duplicate customer id in customers.csv: {customer.id!r}")
        by_id[customer.id] = customer
        customers.append(customer)
    return tuple(customers), by_id


def get_item(sku):
    """Return the Item with this SKU, or None if there is no such item."""
    _, by_sku = _items()
    return by_sku.get(sku)


def get_customer(customer_id):
    """Return the Customer with this id, or None if there is no such customer."""
    _, by_id = _customers()
    return by_id.get(customer_id)


def list_items():
    """Return all catalog items in catalog-file order."""
    items, _ = _items()
    return list(items)


def list_customers():
    """Return all customers in customers-file order."""
    customers, _ = _customers()
    return list(customers)
