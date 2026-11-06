"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file:
  catalog.csv   : sku,name,price_cents,category
  customers.csv : id,name,discount_pct,region

Conventions (agreed in topic 'api_interface'):
  * money is int cents; percentages are decimal.Decimal.
  * Unknown SKU / customer -> None (no exceptions for lookups).

Public API:
  get_unit_price(sku) -> int | None
      Catalog unit price in cents (before any customer discount), or None if unknown SKU.
  get_customer(customer_id) -> CustomerInfo | None
      CustomerInfo is a NamedTuple (name: str, discount_percent: Decimal); None if unknown.
  get_customer_region(customer_id) -> str | None
      Region code (e.g. 'TX', 'OR', 'NY') used for sales-tax lookup; None if unknown.
  get_item(sku) -> Item | None
      Full catalog record (sku, name, price_cents, category); None if unknown SKU.
  list_items() -> list[Item]          in catalog.csv order
  list_customer_ids() -> list[str]    in customers.csv order
  discounted_amount_cents(amount_cents, discount_percent) -> int
      amount * (100 - discount_percent) / 100, rounded half up to whole cents.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import NamedTuple, Optional

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"

_HUNDRED = Decimal(100)
_CENT = Decimal("1")


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price_cents: int
    category: str


class CustomerInfo(NamedTuple):
    name: str
    discount_percent: Decimal


@dataclass(frozen=True)
class _CustomerRecord:
    id: str
    name: str
    discount_percent: Decimal
    region: str


def _load_catalog(path: Path) -> dict[str, Item]:
    items: dict[str, Item] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in {path.name}: {sku!r}")
            price = int(row["price_cents"])
            if price < 0:
                raise ValueError(f"negative price for sku {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price_cents=price,
                category=row["category"].strip(),
            )
    return items


def _load_customers(path: Path) -> dict[str, _CustomerRecord]:
    customers: dict[str, _CustomerRecord] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path.name}: {cid!r}")
            discount = Decimal(row["discount_pct"].strip())
            if not Decimal(0) <= discount <= _HUNDRED:
                raise ValueError(f"discount_pct out of range for customer {cid!r}")
            customers[cid] = _CustomerRecord(
                id=cid,
                name=row["name"].strip(),
                discount_percent=discount,
                region=row["region"].strip(),
            )
    return customers


_ITEMS: dict[str, Item] = _load_catalog(_CATALOG_FILE)
_CUSTOMERS: dict[str, _CustomerRecord] = _load_customers(_CUSTOMERS_FILE)


def get_item(sku: str) -> Optional[Item]:
    """Full catalog record for sku, or None if the SKU is unknown."""
    return _ITEMS.get(sku)


def get_unit_price(sku: str) -> Optional[int]:
    """Catalog unit price in integer cents (no customer discount applied), or None if unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item.price_cents


def get_customer(customer_id: str) -> Optional[CustomerInfo]:
    """(name, discount_percent) for a customer, or None if the customer is unknown."""
    rec = _CUSTOMERS.get(customer_id)
    if rec is None:
        return None
    return CustomerInfo(name=rec.name, discount_percent=rec.discount_percent)


def get_customer_region(customer_id: str) -> Optional[str]:
    """Region code of a customer (used for sales-tax lookup), or None if unknown."""
    rec = _CUSTOMERS.get(customer_id)
    return None if rec is None else rec.region


def list_items() -> list[Item]:
    """All catalog items, in catalog.csv order."""
    return list(_ITEMS.values())


def list_customer_ids() -> list[str]:
    """All customer IDs, in customers.csv order."""
    return list(_CUSTOMERS.keys())


def discounted_amount_cents(amount_cents: int, discount_percent: Decimal) -> int:
    """Apply a percentage discount to an integer cent amount, rounding half up to whole cents.

    Uses Decimal, so no binary floating-point error: 705 cents at 15% off = 599.25 -> 599;
    112.5 -> 113 (exact .5 rounds up).
    """
    pct = Decimal(discount_percent)
    if not Decimal(0) <= pct <= _HUNDRED:
        raise ValueError(f"discount_percent must be in [0, 100], got {discount_percent}")
    exact = Decimal(amount_cents) * (_HUNDRED - pct) / _HUNDRED
    return int(exact.quantize(_CENT, rounding=ROUND_HALF_UP))
