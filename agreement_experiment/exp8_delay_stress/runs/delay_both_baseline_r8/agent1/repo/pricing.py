"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file:
  - catalog.csv   : sku,name,price_cents,category
  - customers.csv : id,name,discount_pct,region

Team conventions (followed here):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)        -> Item or None
  get_customer(cid)    -> Customer or None
  list_items()         -> list[Item]   (catalog order)
  list_customers()     -> list[Customer] (file order)
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
    price: float        # dollars, e.g. 12.5 == $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float     # fraction, e.g. 0.10 == 10% discount
    region: str


def _read_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
        return rows


def _load_items() -> List[Item]:
    items = []
    for row in _read_rows(_CATALOG_PATH):
        items.append(
            Item(
                sku=row["sku"],
                name=row["name"],
                price=int(row["price_cents"]) / 100.0,
                category=row["category"],
            )
        )
    return items


def _load_customers() -> List[Customer]:
    customers = []
    for row in _read_rows(_CUSTOMERS_PATH):
        customers.append(
            Customer(
                id=row["id"],
                name=row["name"],
                discount=float(row["discount_pct"]) / 100.0,
                region=row["region"],
            )
        )
    return customers


_ITEMS: List[Item] = _load_items()
_CUSTOMERS: List[Customer] = _load_customers()
_ITEMS_BY_SKU: Dict[str, Item] = {item.sku: item for item in _ITEMS}
_CUSTOMERS_BY_ID: Dict[str, Customer] = {c.id: c for c in _CUSTOMERS}


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with the given SKU, or None if there is no such SKU."""
    return _ITEMS_BY_SKU.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with the given ID, or None if there is no such customer."""
    return _CUSTOMERS_BY_ID.get(customer_id)


def list_items() -> List[Item]:
    """Return all catalog items in catalog file order."""
    return list(_ITEMS)


def list_customers() -> List[Customer]:
    """Return all customers in customer file order."""
    return list(_CUSTOMERS)
