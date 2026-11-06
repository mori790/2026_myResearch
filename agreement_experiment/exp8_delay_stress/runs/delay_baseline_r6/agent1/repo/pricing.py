"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)            -> Item | None
  get_customer(cust_id)    -> Customer | None
  item_price(sku)          -> float | None          unit price in dollars
  item_category(sku)       -> str | None
  customer_discount(cust_id) -> float | None        discount as a fraction (0.10 = 10%)
  customer_region(cust_id)   -> str | None          e.g. "TX", "OR", "NY"
  discounted_unit_price(sku, cust_id) -> float | None
      unit price after the customer's discount, in dollars, NOT rounded
      (rounding policy belongs to the caller / invoice).
  all_items() -> list[Item]
  all_customers() -> list[Customer]
"""

from __future__ import annotations

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
    price: float      # dollars, e.g. 12.5 == $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float   # fraction, e.g. 0.10 == 10%
    region: str


def _load_items(path: str) -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in {path}: {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price=int(row["price_cents"].strip()) / 100.0,  # cents -> dollars
                category=row["category"].strip(),
            )
    return items


def _load_customers(path: str) -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path}: {cid!r}")
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount=int(row["discount_pct"].strip()) / 100.0,  # percent -> fraction
                region=row["region"].strip(),
            )
    return customers


_ITEMS: Dict[str, Item] = _load_items(_CATALOG_PATH)
_CUSTOMERS: Dict[str, Customer] = _load_customers(_CUSTOMERS_PATH)


def get_item(sku: str) -> Optional[Item]:
    return _ITEMS.get(sku)


def get_customer(cust_id: str) -> Optional[Customer]:
    return _CUSTOMERS.get(cust_id)


def item_price(sku: str) -> Optional[float]:
    item = _ITEMS.get(sku)
    return None if item is None else item.price


def item_category(sku: str) -> Optional[str]:
    item = _ITEMS.get(sku)
    return None if item is None else item.category


def customer_discount(cust_id: str) -> Optional[float]:
    customer = _CUSTOMERS.get(cust_id)
    return None if customer is None else customer.discount


def customer_region(cust_id: str) -> Optional[str]:
    customer = _CUSTOMERS.get(cust_id)
    return None if customer is None else customer.region


def discounted_unit_price(sku: str, cust_id: str) -> Optional[float]:
    """Unit price after the customer's discount. None if sku or customer is unknown."""
    price = item_price(sku)
    discount = customer_discount(cust_id)
    if price is None or discount is None:
        return None
    return price * (1.0 - discount)


def all_items() -> List[Item]:
    return list(_ITEMS.values())


def all_customers() -> List[Customer]:
    return list(_CUSTOMERS.values())
