"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category
  - customers.csv : id, name, discount_pct, region

Team conventions (followed here):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API (PRICING_API v1, committed in the shared decision log):
  get_item(sku)             -> Item or None
  get_customer(customer_id) -> Customer or None
  list_items()              -> list[Item]     (catalog file order)
  list_customers()          -> list[Customer] (customer file order)
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_PATH = _DATA_DIR / "catalog.csv"
_CUSTOMERS_PATH = _DATA_DIR / "customers.csv"


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price: float  # dollars, e.g. 12.5 == $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float  # fraction, e.g. 0.10 == 10% discount
    region: str


def _load_items() -> List[Item]:
    items = []
    with _CATALOG_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append(
                Item(
                    sku=row["sku"].strip(),
                    name=row["name"].strip(),
                    price=int(row["price_cents"]) / 100.0,
                    category=row["category"].strip(),
                )
            )
    return items


def _load_customers() -> List[Customer]:
    customers = []
    with _CUSTOMERS_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customers.append(
                Customer(
                    id=row["id"].strip(),
                    name=row["name"].strip(),
                    discount=int(row["discount_pct"]) / 100.0,
                    region=row["region"].strip(),
                )
            )
    return customers


_ITEMS: List[Item] = _load_items()
_CUSTOMERS: List[Customer] = _load_customers()
_ITEMS_BY_SKU = {item.sku: item for item in _ITEMS}
_CUSTOMERS_BY_ID = {c.id: c for c in _CUSTOMERS}


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if there is no such SKU."""
    return _ITEMS_BY_SKU.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS_BY_ID.get(customer_id)


def list_items() -> List[Item]:
    """Return all catalog items in catalog file order."""
    return list(_ITEMS)


def list_customers() -> List[Customer]:
    """Return all customers in customer file order."""
    return list(_CUSTOMERS)
