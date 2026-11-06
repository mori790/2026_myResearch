"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed team decisions followed here:
- money_representation v2: money is integer cents (1250 = $12.50).
- percent_representation v2: percentages are percent numbers (10 = 10%).
- pricing_api v2: get_item / get_customer return a record or None; pricing applies
  no discounts or tax.
- not_found_signal v2: pricing lookups return None on a miss; they do not raise.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    unit_price: int  # integer cents, e.g. 1250 = $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount_pct: float  # percent number, e.g. 10 = 10%
    region: str  # e.g. "TX", as used in data_tax/rates.csv


def _read_rows(filename: str):
    with open(_DATA_DIR / filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_items() -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    for row in _read_rows("catalog.csv"):
        sku = row["sku"].strip()
        if sku in items:
            raise ValueError(f"duplicate sku in catalog.csv: {sku!r}")
        items[sku] = Item(
            sku=sku,
            name=row["name"].strip(),
            unit_price=int(row["price_cents"]),
            category=row["category"].strip(),
        )
    return items


def _load_customers() -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    for row in _read_rows("customers.csv"):
        cid = row["id"].strip()
        if cid in customers:
            raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
        customers[cid] = Customer(
            id=cid,
            name=row["name"].strip(),
            discount_pct=float(row["discount_pct"]),
            region=row["region"].strip(),
        )
    return customers


_ITEMS: Dict[str, Item] = _load_items()
_CUSTOMERS: Dict[str, Customer] = _load_customers()


def get_item(sku: str) -> Optional[Item]:
    """Return the Item for `sku`, or None if no such SKU exists."""
    return _ITEMS.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer for `customer_id`, or None if no such customer exists."""
    return _CUSTOMERS.get(customer_id)
