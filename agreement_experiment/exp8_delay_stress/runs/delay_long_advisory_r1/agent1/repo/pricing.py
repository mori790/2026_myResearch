"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Implements the committed decision PRICING_API v2:

    get_item(sku: str) -> {"sku": str, "name": str, "price_cents": int, "category": str}
        Raises KeyError if the sku is unknown.

    get_customer(customer_id: str) -> {"id": str, "name": str,
                                       "discount_pct": number, "region": str}
        discount_pct is a percent number (10 means 10%).
        Raises KeyError if the customer id is unknown.

Money is integer cents. This module does no tax computation.
The data files are in data_pricing/ next to this file.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")

_items = None      # dict: sku -> item dict
_customers = None  # dict: customer id -> customer dict


def _parse_number(text):
    """Parse a CSV numeric field: int if it is integral, otherwise float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items():
    global _items
    if _items is None:
        items = {}
        with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sku = row["sku"].strip()
                items[sku] = {
                    "sku": sku,
                    "name": row["name"].strip(),
                    "price_cents": int(row["price_cents"]),
                    "category": row["category"].strip(),
                }
        _items = items
    return _items


def _load_customers():
    global _customers
    if _customers is None:
        customers = {}
        with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row["id"].strip()
                customers[cid] = {
                    "id": cid,
                    "name": row["name"].strip(),
                    "discount_pct": _parse_number(row["discount_pct"]),
                    "region": row["region"].strip(),
                }
        _customers = customers
    return _customers


def get_item(sku):
    """Return item info for sku as a new dict. Raises KeyError if unknown."""
    try:
        item = _load_items()[sku]
    except KeyError:
        raise KeyError(f"unknown sku: {sku!r}") from None
    return dict(item)


def get_customer(customer_id):
    """Return customer info for customer_id as a new dict. Raises KeyError if unknown."""
    try:
        customer = _load_customers()[customer_id]
    except KeyError:
        raise KeyError(f"unknown customer id: {customer_id!r}") from None
    return dict(customer)
