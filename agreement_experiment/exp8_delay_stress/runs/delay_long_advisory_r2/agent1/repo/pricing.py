"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Shared API (committed decision "pricing_api" v2):
    get_item(sku: str) -> dict | None
        {"sku": str, "name": str, "price": int (cents, 1250 = $12.50), "category": str}
        Returns None if the sku is unknown. Price 0 is a valid price, so None
        (not 0) is the unknown-sku signal.
    get_customer(customer_id: str) -> dict | None
        {"id": str, "name": str, "discount": number (percent, 10 = 10%), "region": str}
        Returns None if the customer id is unknown.

This module only supplies prices and customer data. It does not apply discounts,
round amounts, or compute tax.

The data files are in data_pricing/ next to this file.
"""

import csv
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"


def _parse_number(text):
    """Return an int when the text is an integer, otherwise a float."""
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"]
            if sku in items:
                raise ValueError(f"duplicate sku {sku!r} in {path}")
            items[sku] = {
                "sku": sku,
                "name": row["name"],
                "price": int(row["price_cents"]),
                "category": row["category"],
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"]
            if cid in customers:
                raise ValueError(f"duplicate customer id {cid!r} in {path}")
            customers[cid] = {
                "id": cid,
                "name": row["name"],
                "discount": _parse_number(row["discount_pct"]),
                "region": row["region"],
            }
    return customers


_ITEMS = _load_items(_DATA_DIR / "catalog.csv")
_CUSTOMERS = _load_customers(_DATA_DIR / "customers.csv")


def get_item(sku):
    """Return a copy of the item record for sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for customer_id, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
