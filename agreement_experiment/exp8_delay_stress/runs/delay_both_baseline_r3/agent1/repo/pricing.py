"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team convention (followed here):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku: str) -> Item | None
  get_customer(customer_id: str) -> Customer | None
  list_items() -> list[Item]          (catalog order)
  list_customers() -> list[Customer]  (file order)

Item and Customer are frozen dataclasses (read-only records).
"""

import csv
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


@dataclass(frozen=True)
class Item:
    """A catalog item.

    sku:      unique item code, e.g. "A"
    name:     display name, e.g. "Notebook"
    price:    unit price in dollars, e.g. 12.5 for $12.50
    category: e.g. "stationery", "bags", "food"
    """

    sku: str
    name: str
    price: float
    category: str


@dataclass(frozen=True)
class Customer:
    """A customer record.

    id:       unique customer code, e.g. "C1"
    name:     display name, e.g. "Alice"
    discount: customer discount as a fraction, e.g. 0.10 for 10%
    region:   region code used by the tax module, e.g. "TX"
    """

    id: str
    name: str
    discount: float
    region: str


def _read_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {k.strip(): (v.strip() if v is not None else "") for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


@lru_cache(maxsize=1)
def _load_items() -> tuple[tuple[Item, ...], dict[str, Item]]:
    items = []
    by_sku: dict[str, Item] = {}
    for row in _read_rows(_CATALOG_PATH):
        item = Item(
            sku=row["sku"],
            name=row["name"],
            price=int(row["price_cents"]) / 100.0,  # cents -> dollars
            category=row["category"],
        )
        if item.sku in by_sku:
            raise ValueError(f"duplicate SKU in catalog.csv: {item.sku!r}")
        items.append(item)
        by_sku[item.sku] = item
    return tuple(items), by_sku


@lru_cache(maxsize=1)
def _load_customers() -> tuple[tuple[Customer, ...], dict[str, Customer]]:
    customers = []
    by_id: dict[str, Customer] = {}
    for row in _read_rows(_CUSTOMERS_PATH):
        customer = Customer(
            id=row["id"],
            name=row["name"],
            discount=float(row["discount_pct"]) / 100.0,  # percent -> fraction
            region=row["region"],
        )
        if customer.id in by_id:
            raise ValueError(f"duplicate customer id in customers.csv: {customer.id!r}")
        customers.append(customer)
        by_id[customer.id] = customer
    return tuple(customers), by_id


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if there is no such item."""
    _, by_sku = _load_items()
    return by_sku.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such customer."""
    _, by_id = _load_customers()
    return by_id.get(customer_id)


def list_items() -> list[Item]:
    """Return all catalog items in catalog-file order."""
    items, _ = _load_items()
    return list(items)


def list_customers() -> list[Customer]:
    """Return all customers in customers-file order."""
    customers, _ = _load_customers()
    return list(customers)
