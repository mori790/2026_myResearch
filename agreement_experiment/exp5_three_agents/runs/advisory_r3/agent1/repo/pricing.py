"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules. Implements the
committed decisions pricing_api_v2 and customer_region in the shared log:

    get_unit_price_cents(sku)            -> int | None      (price in cents)
    get_customer_discount_percent(cid)   -> Decimal | None  (e.g. Decimal("10"))
    get_customer_region(cid)             -> str | None      (e.g. "TX")
    get_item_category(sku)               -> str | None      (e.g. "stationery")

Unknown SKUs and customer IDs return None; these functions never raise for
them. Monetary values are integer cents. Percentages are decimal.Decimal.

The data files live in data_pricing/ next to this module and are loaded
relative to this file, so the module works from any working directory.
"""

import csv
import os
from decimal import Decimal, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")

__all__ = [
    "get_unit_price_cents",
    "get_customer_discount_percent",
    "get_customer_region",
    "get_item_category",
]


def _read_rows(path):
    """Yield each data row of a CSV file as a dict, with stripped string values."""
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield {k: (v or "").strip() for k, v in row.items() if k is not None}


def _load_catalog(path):
    """Return {sku: {"price_cents": int, "category": str}}."""
    items = {}
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"{path}: duplicate sku {sku!r}")
        price_cents = int(row["price_cents"])
        if price_cents < 0:
            raise ValueError(f"{path}: negative price for sku {sku!r}")
        items[sku] = {"price_cents": price_cents, "category": row["category"]}
    return items


def _load_customers(path):
    """Return {customer_id: {"discount_percent": Decimal, "region": str}}."""
    customers = {}
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"{path}: duplicate customer id {cid!r}")
        try:
            discount = Decimal(row["discount_pct"])
        except InvalidOperation as exc:
            raise ValueError(
                f"{path}: bad discount_pct {row['discount_pct']!r} for customer {cid!r}"
            ) from exc
        if not (Decimal(0) <= discount <= Decimal(100)):
            raise ValueError(f"{path}: discount out of range for customer {cid!r}")
        customers[cid] = {"discount_percent": discount, "region": row["region"].upper()}
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_unit_price_cents(sku):
    """Return the unit price of ``sku`` in integer cents, or None if unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item["price_cents"]


def get_customer_discount_percent(customer_id):
    """Return the customer's discount as a Decimal percentage, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer["discount_percent"]


def get_customer_region(customer_id):
    """Return the customer's two-letter uppercase state code, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer["region"]


def get_item_category(sku):
    """Return the category string of ``sku`` (as in catalog.csv), or None if unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item["category"]
