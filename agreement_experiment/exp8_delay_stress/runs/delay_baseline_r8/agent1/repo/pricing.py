"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku,name,price_cents,category
  - customers.csv : id,name,discount_pct,region

Team conventions (applied here, so callers never see the raw file units):
  - Money amounts are floats in dollars (1250 cents -> 12.5).
  - Percentages are fractions (discount_pct 10 -> 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)          -> Item or None
  get_customer(cust_id)  -> Customer or None
  list_items()           -> list[Item]   (catalog order)
  list_customers()       -> list[Customer] (file order)
"""

import csv
import os
from dataclasses import dataclass
from functools import lru_cache

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.csv")
CUSTOMERS_PATH = os.path.join(DATA_DIR, "customers.csv")


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
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip surrounding whitespace from every field.
            yield {k.strip(): (v or "").strip() for k, v in row.items() if k is not None}


def _parse_item(row):
    return Item(
        sku=row["sku"],
        name=row["name"],
        price=int(row["price_cents"]) / 100.0,
        category=row["category"],
    )


def _parse_customer(row):
    return Customer(
        id=row["id"],
        name=row["name"],
        discount=int(row["discount_pct"]) / 100.0,
        region=row["region"],
    )


@lru_cache(maxsize=1)
def _load_items():
    items = {}
    for row in _read_rows(CATALOG_PATH):
        item = _parse_item(row)
        if item.sku in items:
            raise ValueError(f"duplicate SKU in catalog.csv: {item.sku!r}")
        items[item.sku] = item
    return items


@lru_cache(maxsize=1)
def _load_customers():
    customers = {}
    for row in _read_rows(CUSTOMERS_PATH):
        customer = _parse_customer(row)
        if customer.id in customers:
            raise ValueError(f"duplicate customer id in customers.csv: {customer.id!r}")
        customers[customer.id] = customer
    return customers


def get_item(sku):
    """Return the Item with the given SKU, or None if it does not exist."""
    return _load_items().get(sku)


def get_customer(cust_id):
    """Return the Customer with the given id, or None if it does not exist."""
    return _load_customers().get(cust_id)


def list_items():
    """Return all catalog items in catalog file order."""
    return list(_load_items().values())


def list_customers():
    """Return all customers in customer file order."""
    return list(_load_customers().values())
