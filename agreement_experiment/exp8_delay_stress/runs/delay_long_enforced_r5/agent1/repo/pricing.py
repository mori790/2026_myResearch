"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Interface (committed decision ``pricing_api`` v2):
    get_item(sku) -> Item | None
    get_customer(customer_id) -> Customer | None
    list_items() -> list[Item]
    list_customers() -> list[Customer]

Units (team standard): money is a float in dollars (12.5 means $12.50);
percentages are fractions (0.10 means 10%). Read-only accessors
``Item.price_cents`` and ``Customer.discount_pct`` are provided for consumers
that need integer cents or percent numbers.

This module only supplies data. It does not apply discounts, quantities or tax.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_PATH = _DATA_DIR / "catalog.csv"
_CUSTOMERS_PATH = _DATA_DIR / "customers.csv"


@dataclass(frozen=True)
class Item:
    """A catalog item. ``price`` is the unit price in dollars."""

    sku: str
    name: str
    price: float
    category: str

    @property
    def price_cents(self) -> int:
        """Unit price as integer cents (e.g. 12.5 dollars -> 1250)."""
        return round(self.price * 100)


@dataclass(frozen=True)
class Customer:
    """A customer. ``discount`` is a fraction (0.10 means 10%)."""

    id: str
    name: str
    discount: float
    region: str

    @property
    def discount_pct(self) -> float:
        """Discount as a percent number (0.10 -> 10.0). Float noise is removed."""
        return round(self.discount * 100, 9)


def _read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append(
                {k.strip(): (v or "").strip() for k, v in row.items() if k is not None}
            )
        return rows


def _load_items(path: Path) -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"{path.name}: duplicate sku {sku!r}")
        # Stored in cents in the CSV; converted to float dollars here.
        # Integer true division is correctly rounded, so 1250 -> 12.5 exactly.
        price_cents = int(row["price_cents"])
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=price_cents / 100,
            category=row["category"],
        )
    return items


def _load_customers(path: Path) -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"{path.name}: duplicate customer id {cid!r}")
        # Stored as a percent number in the CSV; converted to a fraction here.
        customers[cid] = Customer(
            id=cid,
            name=row["name"],
            discount=float(row["discount_pct"]) / 100,
            region=row["region"],
        )
    return customers


_ITEMS: Dict[str, Item] = _load_items(_CATALOG_PATH)
_CUSTOMERS: Dict[str, Customer] = _load_customers(_CUSTOMERS_PATH)


def get_item(sku: str) -> Optional[Item]:
    """Return the item with this SKU, or None if the catalog has no such SKU."""
    return _ITEMS.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the customer with this id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def list_items() -> List[Item]:
    """All catalog items, in catalog file order."""
    return list(_ITEMS.values())


def list_customers() -> List[Customer]:
    """All customers, in customer file order."""
    return list(_CUSTOMERS.values())
