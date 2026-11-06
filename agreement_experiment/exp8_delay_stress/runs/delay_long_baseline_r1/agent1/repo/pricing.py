"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku,name,price_cents,category
  - customers.csv : id,name,discount_pct,region

Team conventions (followed everywhere in this module):
  - Money amounts are floats in dollars (1250 cents -> 12.5).
  - Percentages are fractions (10 -> 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)             -> Item or None
  get_customer(customer_id) -> Customer or None
  list_items()              -> list[Item]     (catalog file order)
  list_customers()          -> list[Customer] (file order)
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
    region: str       # e.g. "TX", "OR", "NY" (passed through unchanged for tax.py)


def _read_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = []
        for row in csv.DictReader(f):
            rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
        return rows


def _load_items(path: str) -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in catalog: {sku!r}")
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=round(int(row["price_cents"]) / 100, 2),
            category=row["category"],
        )
    return items


def _load_customers(path: str) -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id: {cid!r}")
        customers[cid] = Customer(
            id=cid,
            name=row["name"],
            discount=round(float(row["discount_pct"]) / 100, 4),
            region=row["region"],
        )
    return customers


_ITEMS: Dict[str, Item] = _load_items(_CATALOG_PATH)
_CUSTOMERS: Dict[str, Customer] = _load_customers(_CUSTOMERS_PATH)


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if it is not in the catalog."""
    return _ITEMS.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this ID, or None if unknown."""
    return _CUSTOMERS.get(customer_id)


def list_items() -> List[Item]:
    """All catalog items, in file order."""
    return list(_ITEMS.values())


def list_customers() -> List[Customer]:
    """All customers, in file order."""
    return list(_CUSTOMERS.values())
