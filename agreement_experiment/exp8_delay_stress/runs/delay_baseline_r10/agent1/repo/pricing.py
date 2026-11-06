"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)            -> Item | None
  get_customer(customer_id) -> Customer | None
  list_items()             -> list[Item]     (catalog order)
  list_customers()         -> list[Customer] (file order)
  unit_price(sku)          -> float | None   (dollars; None if sku unknown)
  discount_rate(customer_id) -> float | None (fraction, e.g. 0.10; None if unknown)
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
    discount: float   # fraction, e.g. 0.10 == 10% discount
    region: str       # e.g. "TX", "OR", "NY"


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            item = Item(
                sku=sku,
                name=row["name"].strip(),
                price=int(row["price_cents"]) / 100.0,  # cents -> dollars
                category=row["category"].strip(),
            )
            items[sku] = item
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customer = Customer(
                id=cid,
                name=row["name"].strip(),
                discount=float(row["discount_pct"]) / 100.0,  # percent -> fraction
                region=row["region"].strip(),
            )
            customers[cid] = customer
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item with this SKU, or None if it does not exist."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer with this id, or None if it does not exist."""
    return _CUSTOMERS.get(customer_id)


def list_items():
    """Return all items in catalog order."""
    return list(_ITEMS.values())


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())


def unit_price(sku):
    """Return the unit price in dollars, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item.price


def discount_rate(customer_id):
    """Return the customer's discount as a fraction, or None if the customer is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer.discount
