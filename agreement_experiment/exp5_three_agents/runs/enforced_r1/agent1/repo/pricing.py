"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
Data files are in data_pricing/ next to this file:
  - catalog.csv   : sku,name,price_cents,category
  - customers.csv : id,name,discount_pct,region

Interface (committed decision PRICING_API v2):
  Item, Customer                        dataclasses
  get_item(sku) -> Item                 raises KeyError if unknown
  get_customer(customer_id) -> Customer raises KeyError if unknown
  all_items() -> list[Item]             catalog order
  all_customers() -> list[Customer]     file order
  discount_cents(customer_id, subtotal_cents) -> int
      cents to subtract: (subtotal_cents * discount_pct + 50) // 100
      (round half up). This is the amount to subtract, not the discounted total.

All money is integer cents. This module does not compute tax.
"""

import csv
import os
from dataclasses import dataclass
from typing import Dict, List

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_FILE = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_FILE = os.path.join(_DATA_DIR, "customers.csv")


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price_cents: int
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount_pct: int
    region: str


def _load_items(path: str) -> List[Item]:
    items: List[Item] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append(
                Item(
                    sku=row["sku"].strip(),
                    name=row["name"].strip(),
                    price_cents=int(row["price_cents"]),
                    category=row["category"].strip(),
                )
            )
    return items


def _load_customers(path: str) -> List[Customer]:
    customers: List[Customer] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pct = int(row["discount_pct"])
            if not 0 <= pct <= 100:
                raise ValueError(f"discount_pct out of range for customer {row['id']}: {pct}")
            customers.append(
                Customer(
                    id=row["id"].strip(),
                    name=row["name"].strip(),
                    discount_pct=pct,
                    region=row["region"].strip(),
                )
            )
    return customers


_ITEMS: List[Item] = _load_items(_CATALOG_FILE)
_CUSTOMERS: List[Customer] = _load_customers(_CUSTOMERS_FILE)
_ITEMS_BY_SKU: Dict[str, Item] = {item.sku: item for item in _ITEMS}
_CUSTOMERS_BY_ID: Dict[str, Customer] = {c.id: c for c in _CUSTOMERS}


def get_item(sku: str) -> Item:
    """Return the Item with the given SKU. Raises KeyError if unknown."""
    return _ITEMS_BY_SKU[sku]


def get_customer(customer_id: str) -> Customer:
    """Return the Customer with the given id. Raises KeyError if unknown."""
    return _CUSTOMERS_BY_ID[customer_id]


def all_items() -> List[Item]:
    """All items in catalog order."""
    return list(_ITEMS)


def all_customers() -> List[Customer]:
    """All customers in file order."""
    return list(_CUSTOMERS)


def discount_cents(customer_id: str, subtotal_cents: int) -> int:
    """Discount amount in cents to subtract from subtotal_cents for this customer.

    Round half up: (subtotal_cents * discount_pct + 50) // 100.
    Raises KeyError if the customer is unknown.
    """
    pct = get_customer(customer_id).discount_pct
    return (subtotal_cents * pct + 50) // 100
