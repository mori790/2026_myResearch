"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku) -> Item | None
  get_customer(customer_id) -> Customer | None
  list_items() -> list[Item]          (catalog order)
  list_customers() -> list[Customer]  (file order)
  discounted_unit_price(customer_id, sku) -> float | None
      Unit price in dollars after the customer's discount, or None if the
      customer or the item does not exist.
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
    price: float      # dollars, e.g. 12.5 == $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float   # fraction, e.g. 0.10 == 10%
    region: str


def _load_items():
    items = {}
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            item = Item(
                sku=row["sku"].strip(),
                name=row["name"].strip(),
                price=int(row["price_cents"]) / 100.0,
                category=row["category"].strip(),
            )
            items[item.sku] = item
    return items


def _load_customers():
    customers = {}
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customer = Customer(
                id=row["id"].strip(),
                name=row["name"].strip(),
                discount=int(row["discount_pct"]) / 100.0,
                region=row["region"].strip(),
            )
            customers[customer.id] = customer
    return customers


# Loaded once at import time; the data files are small and read-only.
_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return the Item with this SKU, or None if it does not exist."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer with this ID, or None if it does not exist."""
    return _CUSTOMERS.get(customer_id)


def list_items():
    """Return all items in catalog order."""
    return list(_ITEMS.values())


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())


def discounted_unit_price(customer_id, sku):
    """Return the unit price in dollars after the customer's discount.

    Returns None if either the customer or the item is not found.
    """
    customer = get_customer(customer_id)
    item = get_item(sku)
    if customer is None or item is None:
        return None
    return round(item.price * (1.0 - customer.discount), 2)
