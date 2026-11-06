"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed everywhere in this module):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)        -> Item or None
  get_customer(cid)    -> Customer or None
  list_items()         -> list[Item]     (catalog order)
  list_customers()     -> list[Customer] (file order)

Item and Customer are frozen dataclasses, so callers cannot change the
loaded data by accident.

Raw data format (as stored in the CSV files):
  catalog.csv   : sku, name, price_cents, category   (price in integer cents)
  customers.csv : id, name, discount_pct, region     (discount as whole percent)
"""

import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


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


def _cents_to_dollars(cents_text: str) -> float:
    # Integer cents -> float dollars. Division by 100 of an int is exact
    # enough for money at this scale; round to 2 places to avoid noise.
    return round(int(cents_text.strip()) / 100, 2)


def _percent_to_fraction(percent_text: str) -> float:
    # Whole percent -> fraction, e.g. "10" -> 0.10
    return round(int(percent_text.strip()) / 100, 4)


def _load_items(path: str) -> List[Item]:
    items: List[Item] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("sku"):
                continue
            items.append(Item(
                sku=row["sku"].strip(),
                name=row["name"].strip(),
                price=_cents_to_dollars(row["price_cents"]),
                category=row["category"].strip(),
            ))
    return items


def _load_customers(path: str) -> List[Customer]:
    customers: List[Customer] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("id"):
                continue
            customers.append(Customer(
                id=row["id"].strip(),
                name=row["name"].strip(),
                discount=_percent_to_fraction(row["discount_pct"]),
                region=row["region"].strip(),
            ))
    return customers


_ITEMS: List[Item] = _load_items(_CATALOG_PATH)
_ITEMS_BY_SKU: Dict[str, Item] = {item.sku: item for item in _ITEMS}

_CUSTOMERS: List[Customer] = _load_customers(_CUSTOMERS_PATH)
_CUSTOMERS_BY_ID: Dict[str, Customer] = {c.id: c for c in _CUSTOMERS}


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if there is no such item."""
    return _ITEMS_BY_SKU.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS_BY_ID.get(customer_id)


def list_items() -> List[Item]:
    """Return all catalog items in catalog order."""
    return list(_ITEMS)


def list_customers() -> List[Customer]:
    """Return all customers in file order."""
    return list(_CUSTOMERS)
