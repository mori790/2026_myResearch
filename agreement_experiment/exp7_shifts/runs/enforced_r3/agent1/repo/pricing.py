"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category
  - customers.csv : id, name, discount_pct, region

Team coding standard (applied here):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API (committed as decision "pricing_api" v1):
  get_item(sku)             -> Item or None
  get_price(sku)            -> float (dollars) or None
  get_customer(customer_id) -> Customer or None
  list_items()              -> list[Item]     (catalog order)
  list_customers()          -> list[Customer] (file order)

  Item.sku, Item.name, Item.price (float dollars), Item.category
  Customer.id, Customer.name, Customer.discount_rate (fraction), Customer.region
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price: float  # dollars, e.g. 12.5 means $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount_rate: float  # fraction, e.g. 0.10 means 10%
    region: str


def _load_items(path: Path) -> List[Item]:
    items: List[Item] = []
    seen = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in seen:
                raise ValueError(f"duplicate SKU in catalog: {sku!r}")
            seen.add(sku)
            cents = int(row["price_cents"])
            items.append(Item(
                sku=sku,
                name=row["name"].strip(),
                price=cents / 100.0,
                category=row["category"].strip(),
            ))
    return items


def _load_customers(path: Path) -> List[Customer]:
    customers: List[Customer] = []
    seen = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in seen:
                raise ValueError(f"duplicate customer id: {cid!r}")
            seen.add(cid)
            pct = float(row["discount_pct"])
            customers.append(Customer(
                id=cid,
                name=row["name"].strip(),
                discount_rate=pct / 100.0,
                region=row["region"].strip(),
            ))
    return customers


_ITEMS: List[Item] = _load_items(_CATALOG_FILE)
_CUSTOMERS: List[Customer] = _load_customers(_CUSTOMERS_FILE)
_ITEMS_BY_SKU: Dict[str, Item] = {item.sku: item for item in _ITEMS}
_CUSTOMERS_BY_ID: Dict[str, Customer] = {c.id: c for c in _CUSTOMERS}


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if there is no such item."""
    return _ITEMS_BY_SKU.get(sku)


def get_price(sku: str) -> Optional[float]:
    """Return the unit price in dollars for this SKU, or None if unknown."""
    item = _ITEMS_BY_SKU.get(sku)
    return None if item is None else item.price


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS_BY_ID.get(customer_id)


def list_items() -> List[Item]:
    """Return all catalog items in catalog-file order."""
    return list(_ITEMS)


def list_customers() -> List[Customer]:
    """Return all customers in customers-file order."""
    return list(_CUSTOMERS)
