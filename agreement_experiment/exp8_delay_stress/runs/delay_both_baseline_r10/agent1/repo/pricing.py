"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku: str) -> Item | None
  get_customer(customer_id: str) -> Customer | None
  list_items() -> list[Item]           (catalog order)
  list_customers() -> list[Customer]   (file order)

  Item.sku, Item.name, Item.price (dollars, float), Item.category
  Customer.id, Customer.name, Customer.discount (fraction, e.g. 0.10), Customer.region
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
    price: float  # dollars
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float  # fraction, e.g. 0.10 for 10%
    region: str


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {(k or "").strip(): (v or "").strip() for k, v in row.items()}


def _load_items(path):
    items = {}
    order = []
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in {path}: {sku!r}")
        # price_cents is an integer number of cents; convert to dollars.
        price = round(int(row["price_cents"]) / 100, 2)
        items[sku] = Item(sku=sku, name=row["name"], price=price, category=row["category"])
        order.append(sku)
    return items, order


def _load_customers(path):
    customers = {}
    order = []
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id in {path}: {cid!r}")
        # discount_pct is a percentage number (10 means 10%); convert to a fraction.
        discount = round(float(row["discount_pct"]) / 100, 6)
        customers[cid] = Customer(id=cid, name=row["name"], discount=discount, region=row["region"])
        order.append(cid)
    return customers, order


_ITEMS, _ITEM_ORDER = _load_items(_CATALOG_PATH)
_CUSTOMERS, _CUSTOMER_ORDER = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item with the given SKU, or None if there is no such item."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer with the given id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def list_items():
    """Return all items in catalog order."""
    return [_ITEMS[sku] for sku in _ITEM_ORDER]


def list_customers():
    """Return all customers in file order."""
    return [_CUSTOMERS[cid] for cid in _CUSTOMER_ORDER]
