"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku) -> Item | None
  get_customer(customer_id) -> Customer | None
  list_items() -> list[Item]
  list_customers() -> list[Customer]
  discounted_unit_price(sku, customer_id) -> float | None
      Unit price in dollars after the customer's discount, rounded to cents.
      Returns None if the sku or the customer is unknown.
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
    price: float      # list price in dollars (e.g. 12.5 == $12.50)
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float   # fraction (0.10 == 10% discount)
    region: str       # e.g. "TX", "OR", "NY"; used by tax rules in tax.py


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price=int(row["price_cents"]) / 100.0,
                category=row["category"].strip(),
            )
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount=int(row["discount_pct"]) / 100.0,
                region=row["region"].strip(),
            )
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item with this sku, or None if there is no such item."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def list_items():
    """Return all items, in catalog order."""
    return list(_ITEMS.values())


def list_customers():
    """Return all customers, in file order."""
    return list(_CUSTOMERS.values())


def discounted_unit_price(sku, customer_id):
    """Return the unit price in dollars after the customer's discount, rounded to cents.

    Returns None if either the sku or the customer is unknown.
    """
    item = get_item(sku)
    customer = get_customer(customer_id)
    if item is None or customer is None:
        return None
    return round(item.price * (1.0 - customer.discount), 2)
