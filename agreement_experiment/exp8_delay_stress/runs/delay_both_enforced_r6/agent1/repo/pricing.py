"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Implements the committed decision `pricing-api` (v2):
- Money: float dollars (12.5 = $12.50), converted from catalog price_cents / 100.
- Percentages: fractions (0.10 = 10%), converted from customers discount_pct / 100.
- Not found: None.

Public API:
- get_item(sku) -> Item | None
- get_customer(customer_id) -> Customer | None
- get_price(sku) -> float | None
- get_discount(customer_id) -> float | None
- all_items() -> list[Item]
- all_customers() -> list[Customer]
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
        rows = []
        for row in csv.DictReader(f):
            rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
        return rows


def _load_items():
    items = {}
    for row in _read_rows(_CATALOG_PATH):
        sku = row["sku"]
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=round(int(row["price_cents"]) / 100, 2),  # cents -> dollars
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
            discount=round(int(row["discount_pct"]) / 100, 4),  # percent -> fraction
            region=row["region"],
        )
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return the Item for `sku`, or None if no such item exists."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer for `customer_id`, or None if no such customer exists."""
    return _CUSTOMERS.get(customer_id)


def get_price(sku):
    """Return the unit price in dollars for `sku`, or None if the item is unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item.price


def get_discount(customer_id):
    """Return the customer's discount as a fraction, or None if the customer is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer.discount


def all_items():
    """Return all items, in catalog order."""
    return list(_ITEMS.values())


def all_customers():
    """Return all customers, in file order."""
    return list(_CUSTOMERS.values())
