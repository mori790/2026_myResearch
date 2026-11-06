"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file.

Units (committed decisions money_units v1 and pricing_api v2):
  * Money amounts are integer cents (1250 = $12.50).
  * Percentages are percent numbers (10 = 10%), never fractions.
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku) -> Item | None
  get_customer(customer_id) -> Customer | None
  list_items() -> list[Item]           (catalog order)
  list_customers() -> list[Customer]   (file order)
  get_unit_price_cents(sku) -> int | None
  get_discount_pct(customer_id) -> number | None
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
    price_cents: int  # integer cents, e.g. 1250 means $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount_pct: int  # percent number, e.g. 10 means 10% off
    region: str


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            for row in reader
        ]


def _load_items():
    return [
        Item(
            sku=row["sku"],
            name=row["name"],
            price_cents=int(row["price_cents"]),
            category=row["category"],
        )
        for row in _read_rows(_CATALOG_PATH)
    ]


def _load_customers():
    return [
        Customer(
            id=row["id"],
            name=row["name"],
            discount_pct=int(row["discount_pct"]),
            region=row["region"],
        )
        for row in _read_rows(_CUSTOMERS_PATH)
    ]


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()
_ITEMS_BY_SKU = {item.sku: item for item in _ITEMS}
_CUSTOMERS_BY_ID = {c.id: c for c in _CUSTOMERS}


def get_item(sku):
    """Return the Item for `sku`, or None if no such item exists."""
    return _ITEMS_BY_SKU.get(sku)


def get_customer(customer_id):
    """Return the Customer for `customer_id`, or None if no such customer exists."""
    return _CUSTOMERS_BY_ID.get(customer_id)


def list_items():
    """Return all items in catalog order."""
    return list(_ITEMS)


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS)


def get_unit_price_cents(sku):
    """Return the unit price in integer cents for `sku`, or None if unknown."""
    item = get_item(sku)
    return None if item is None else item.price_cents


def get_discount_pct(customer_id):
    """Return the customer's discount as a percent number (10 = 10%), or None if unknown."""
    customer = get_customer(customer_id)
    return None if customer is None else customer.discount_pct
