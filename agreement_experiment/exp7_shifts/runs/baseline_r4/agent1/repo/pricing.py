"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category
  - customers.csv : id, name, discount_pct, region

Team conventions (followed everywhere in this module):
  - Money amounts are floats in dollars (1250 cents -> 12.5).
  - Percentages are fractions (10 percent -> 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)                 -> dict | None
      {"sku": str, "name": str, "price": float (dollars), "category": str}
  get_price(sku)                -> float | None   (dollars)
  get_customer(customer_id)     -> dict | None
      {"id": str, "name": str, "discount": float (fraction), "region": str}
  get_discount(customer_id)     -> float | None   (fraction, e.g. 0.10)
  get_region(customer_id)       -> str | None
  discounted_price(sku, customer_id) -> float | None
      Unit price in dollars after the customer's discount, rounded to cents.
      Returns None if either the SKU or the customer is unknown.
  list_items()                  -> list[dict]
  list_customers()              -> list[dict]
"""

import csv
import os
from typing import Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items() -> Dict[str, dict]:
    items: Dict[str, dict] = {}
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source stores integer cents; convert to float dollars.
                "price": round(int(row["price_cents"].strip()) / 100, 2),
                "category": row["category"].strip(),
            }
    return items


def _load_customers() -> Dict[str, dict]:
    customers: Dict[str, dict] = {}
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # Source stores whole-number percent; convert to a fraction.
                "discount": round(float(row["discount_pct"].strip()) / 100, 4),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS: Dict[str, dict] = _load_items()
_CUSTOMERS: Dict[str, dict] = _load_customers()


def get_item(sku: str) -> Optional[dict]:
    """Return a copy of the item record for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_price(sku: str) -> Optional[float]:
    """Return the list unit price in dollars for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return item["price"] if item is not None else None


def get_customer(customer_id: str) -> Optional[dict]:
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def get_discount(customer_id: str) -> Optional[float]:
    """Return the customer's discount as a fraction (0.10 = 10%), or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return customer["discount"] if customer is not None else None


def get_region(customer_id: str) -> Optional[str]:
    """Return the customer's region code (e.g. "TX"), or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return customer["region"] if customer is not None else None


def discounted_price(sku: str, customer_id: str) -> Optional[float]:
    """Return the unit price in dollars after the customer's discount, rounded to cents.

    Returns None if the SKU or the customer is unknown.
    """
    price = get_price(sku)
    discount = get_discount(customer_id)
    if price is None or discount is None:
        return None
    return round(price * (1 - discount), 2)


def list_items() -> List[dict]:
    """Return copies of all item records."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers() -> List[dict]:
    """Return copies of all customer records."""
    return [dict(customer) for customer in _CUSTOMERS.values()]
