"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file.

Committed team decisions this module follows:
  - MONEY_REPRESENTATION v2: money is integer cents (1250 means 12.50 dollars).
  - PERCENT_REPRESENTATION v2: percentages are percent numbers (10 means 10%).
  - MISSING_LOOKUP_RESULT v1: a lookup that finds nothing returns None.
  - PRICING_API v2: get_item and get_customer return the dict shapes documented below.

This module computes no tax. Customer region is passed through unchanged to tax.py.
"""

import csv
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"


def _parse_number(text):
    """Parse a CSV number. Integers stay int; decimals become float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_FILE)
_CUSTOMERS = _load_customers(_CUSTOMERS_FILE)


def get_item(sku):
    """Return item info for a SKU, or None if the SKU is unknown.

    Returned dict: {"sku": str, "name": str, "unit_price_cents": int, "category": str}
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for a customer ID, or None if the ID is unknown.

    Returned dict: {"id": str, "name": str, "discount_pct": number, "region": str}
    discount_pct is a percent number (10 means 10%), 0 when there is no discount.
    region is passed unchanged to tax.py (e.g. "TX").
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
