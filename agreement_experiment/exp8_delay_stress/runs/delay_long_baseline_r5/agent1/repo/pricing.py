"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed here):
- Money amounts are floats in dollars (12.5 means $12.50).
- Percentages are fractions (10% is 0.10).
- A lookup that finds nothing returns None.

Public API:
- get_item(sku)           -> Item or None
- get_customer(cust_id)   -> Customer or None
- list_items()            -> list[Item]   (in catalog file order)
- list_customers()        -> list[Customer] (in customer file order)

Item and Customer are frozen dataclasses, so callers can read fields
(item.sku, item.name, item.price, item.category, customer.id,
customer.name, customer.discount, customer.region) but cannot mutate them.
"""

import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

__all__ = ["Item", "Customer", "get_item", "get_customer", "list_items", "list_customers"]

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
    discount: float   # fraction, e.g. 0.10 means 10%
    region: str


def _read_rows(path: str) -> List[Dict[str, str]]:
    # utf-8-sig tolerates a BOM; strip() tolerates stray whitespace around fields.
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for raw in reader:
            rows.append({(k or "").strip(): (v or "").strip() for k, v in raw.items()})
        return rows


def _load_items() -> List[Item]:
    items: List[Item] = []
    seen = set()
    for row in _read_rows(_CATALOG_PATH):
        sku = row["sku"]
        if sku in seen:
            raise ValueError(f"duplicate SKU in catalog.csv: {sku!r}")
        seen.add(sku)
        items.append(Item(
            sku=sku,
            name=row["name"],
            price=round(int(row["price_cents"]) / 100.0, 2),
            category=row["category"],
        ))
    return items


def _load_customers() -> List[Customer]:
    customers: List[Customer] = []
    seen = set()
    for row in _read_rows(_CUSTOMERS_PATH):
        cid = row["id"]
        if cid in seen:
            raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
        seen.add(cid)
        customers.append(Customer(
            id=cid,
            name=row["name"],
            # The file stores whole percents (10 means 10%); convert to a fraction.
            discount=round(float(row["discount_pct"]) / 100.0, 4),
            region=row["region"],
        ))
    return customers


# Loaded once at import time; the data files are small.
_ITEMS: List[Item] = _load_items()
_ITEMS_BY_SKU: Dict[str, Item] = {item.sku: item for item in _ITEMS}
_CUSTOMERS: List[Customer] = _load_customers()
_CUSTOMERS_BY_ID: Dict[str, Customer] = {c.id: c for c in _CUSTOMERS}


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if there is no such SKU."""
    return _ITEMS_BY_SKU.get(sku)


def get_customer(cust_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such id."""
    return _CUSTOMERS_BY_ID.get(cust_id)


def list_items() -> List[Item]:
    """Return all catalog items in file order."""
    return list(_ITEMS)


def list_customers() -> List[Customer]:
    """Return all customers in file order."""
    return list(_CUSTOMERS)
