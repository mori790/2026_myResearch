"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku,name,price_cents,category
  - customers.csv : id,name,discount_pct,region

Conventions (team standard):
  - Money amounts are floats in dollars (1250 cents -> 12.5).
  - Percentages are fractions (10 -> 0.10).
  - A lookup that finds nothing returns None.
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
    price: float  # dollars (team standard)
    category: str

    @property
    def price_cents(self) -> int:
        """Same price as integer cents, for callers that use cents."""
        return round(self.price * 100)


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float  # fraction, e.g. 0.10 for 10% (team standard)
    region: str  # e.g. "TX"; used by tax.py for sales tax lookup

    @property
    def discount_pct(self) -> int:
        """Same discount as a percent number (10 for 10%), for callers that use percents."""
        return round(self.discount * 100)


def _load_items() -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price=int(row["price_cents"]) / 100.0,
                category=row["category"].strip(),
            )
    return items


def _load_customers() -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount=float(row["discount_pct"]) / 100.0,
                region=row["region"].strip(),
            )
    return customers


_ITEMS: Dict[str, Item] = _load_items()
_CUSTOMERS: Dict[str, Customer] = _load_customers()


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with the given SKU, or None if it does not exist."""
    return _ITEMS.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with the given ID, or None if it does not exist."""
    return _CUSTOMERS.get(customer_id)


def list_items() -> List[Item]:
    """Return all items in catalog order."""
    return list(_ITEMS.values())


def list_customers() -> List[Customer]:
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
