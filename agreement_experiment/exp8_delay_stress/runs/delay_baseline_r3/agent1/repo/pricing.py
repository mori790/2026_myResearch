"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category
  - customers.csv : id, name, discount_pct, region

Conventions (team standard):
  - Money amounts are floats in dollars (1250 cents -> 12.5).
  - Percentages are fractions (discount_pct 10 -> 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku) -> Item | None
  get_customer(customer_id) -> Customer | None
  list_items() -> list[Item]
  list_customers() -> list[Customer]
  get_unit_price(sku) -> float | None              # catalog price in dollars
  get_discount(customer_id) -> float | None         # fraction, e.g. 0.10
  get_discounted_price(sku, customer_id) -> float | None
      # unit price after the customer's discount, rounded to cents
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
    price: float      # dollars
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float   # fraction, e.g. 0.10 for 10%
    region: str


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield {k.strip(): (v.strip() if isinstance(v, str) else v)
                   for k, v in row.items() if k is not None}


def _load_items():
    items = {}
    for row in _read_rows(_CATALOG_PATH):
        sku = row["sku"]
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=int(row["price_cents"]) / 100.0,
            category=row["category"],
        )
    return items


def _load_customers():
    customers = {}
    for row in _read_rows(_CUSTOMERS_PATH):
        cid = row["id"]
        customers[cid] = Customer(
            id=cid,
            name=row["name"],
            discount=int(row["discount_pct"]) / 100.0,
            region=row["region"],
        )
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return the Item for sku, or None if it is not in the catalog."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer for customer_id, or None if unknown."""
    return _CUSTOMERS.get(customer_id)


def list_items():
    """Return all catalog items in file order."""
    return list(_ITEMS.values())


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())


def get_unit_price(sku):
    """Return the catalog unit price in dollars, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item.price


def get_discount(customer_id):
    """Return the customer's discount as a fraction, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer.discount


def get_discounted_price(sku, customer_id):
    """Return the unit price after the customer's discount, rounded to cents.

    Returns None if either the sku or the customer is unknown.
    """
    price = get_unit_price(sku)
    discount = get_discount(customer_id)
    if price is None or discount is None:
        return None
    return round(price * (1 - discount), 2)
