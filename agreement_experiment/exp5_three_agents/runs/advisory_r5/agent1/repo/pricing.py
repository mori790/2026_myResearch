"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Committed decisions followed (agree.py):
  - money_units: every money amount is an int in cents (no floats).
  - pricing_api_v2:
      get_item(sku)                -> {"sku", "name", "unit_price_cents", "category"} | None
      get_customer(customer_id)    -> {"id", "name", "region", "discount_percent"} | None
      get_unit_price_cents(sku)    -> int | None
    This module computes no discounts and no tax. The discount is applied by tax.py.

The data files are in data_pricing/ next to this file:
  catalog.csv   : sku, name, price_cents, category
  customers.csv : id, name, discount_pct, region
"""

import csv
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"


def _read_rows(filename):
    """Read a CSV file from data_pricing/ and return its rows as a list of dicts with stripped values."""
    path = _DATA_DIR / filename
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k is not None} for row in reader]


def _load_items():
    items = {}
    for row in _read_rows("catalog.csv"):
        sku = row["sku"]
        if not sku:
            raise ValueError("catalog.csv: empty sku")
        if sku in items:
            raise ValueError(f"catalog.csv: duplicate sku {sku!r}")
        price_cents = int(row["price_cents"])  # ValueError on non-integer text
        if price_cents < 0:
            raise ValueError(f"catalog.csv: negative price for sku {sku!r}")
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            "unit_price_cents": price_cents,
            "category": row["category"],
        }
    return items


def _load_customers():
    customers = {}
    for row in _read_rows("customers.csv"):
        cid = row["id"]
        if not cid:
            raise ValueError("customers.csv: empty id")
        if cid in customers:
            raise ValueError(f"customers.csv: duplicate id {cid!r}")
        discount = int(row["discount_pct"])  # ValueError on non-integer text
        if not 0 <= discount <= 100:
            raise ValueError(f"customers.csv: discount_pct out of 0..100 for id {cid!r}")
        customers[cid] = {
            "id": cid,
            "name": row["name"],
            "region": row["region"],
            "discount_percent": discount,
        }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return a copy of the catalog entry for sku, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_unit_price_cents(sku):
    """Return the unit price in int cents for sku, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return item["unit_price_cents"] if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record, or None if the customer is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
