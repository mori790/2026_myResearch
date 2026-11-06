"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions:
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)             -> Item or None
  get_customer(customer_id) -> Customer or None
  get_unit_price(sku)       -> float (dollars) or None
  get_discount_rate(customer_id) -> float (fraction, e.g. 0.10) or None
  list_items()              -> list[Item]
  list_customers()          -> list[Customer]
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
    unit_price: float  # dollars, e.g. 12.5 == $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    discount_rate: float  # fraction, e.g. 0.10 == 10%
    region: str


_items: Optional[Dict[str, Item]] = None
_customers: Optional[Dict[str, Customer]] = None


def _load_items() -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                # Stored as integer cents in the CSV; converted to dollars.
                unit_price=int(row["price_cents"]) / 100.0,
                category=row["category"].strip(),
            )
    return items


def _load_customers() -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customer_id = row["id"].strip()
            customers[customer_id] = Customer(
                customer_id=customer_id,
                name=row["name"].strip(),
                # Stored as whole percent in the CSV; converted to a fraction.
                discount_rate=float(row["discount_pct"]) / 100.0,
                region=row["region"].strip(),
            )
    return customers


def _get_items() -> Dict[str, Item]:
    global _items
    if _items is None:
        _items = _load_items()
    return _items


def _get_customers() -> Dict[str, Customer]:
    global _customers
    if _customers is None:
        _customers = _load_customers()
    return _customers


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with the given SKU, or None if it does not exist."""
    return _get_items().get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with the given id, or None if it does not exist."""
    return _get_customers().get(customer_id)


def get_unit_price(sku: str) -> Optional[float]:
    """Return the unit price in dollars for a SKU, or None if the SKU is unknown."""
    item = get_item(sku)
    return None if item is None else item.unit_price


def get_discount_rate(customer_id: str) -> Optional[float]:
    """Return the customer's discount as a fraction (0.10 == 10%), or None if unknown."""
    customer = get_customer(customer_id)
    return None if customer is None else customer.discount_rate


def list_items() -> List[Item]:
    """Return all items in catalog order."""
    return list(_get_items().values())


def list_customers() -> List[Customer]:
    """Return all customers in file order."""
    return list(_get_customers().values())
