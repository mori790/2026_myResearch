"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API (committed as decision topic pricing_api v2):
  lookup_item(sku)            -> None or {"sku", "name", "unit_price_cents": int}
  lookup_customer(customer_id)-> None or {"id", "name", "region",
                                          "discount_percent": str,
                                          "tax_percent": str}

All money amounts are integer cents. Percent values are decimal strings
without "%" (e.g. "10", "8.25", "0"); parse them with decimal.Decimal.
Rounding of discounts and tax is done by invoice.py, not here.
"""

import csv
import os
from decimal import Decimal, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: v.strip() for k, v in row.items()} for row in csv.DictReader(f)]


def _check_percent(value, where):
    try:
        Decimal(value)
    except InvalidOperation:
        raise ValueError(f"invalid percent {value!r} in {where}") from None
    return value


def _load_tax():
    tax = {}
    for row in _read_rows("tax.csv"):
        tax[row["region"]] = _check_percent(row["tax_pct"], "tax.csv")
    return tax


def _load_items():
    items = {}
    for row in _read_rows("catalog.csv"):
        items[row["sku"]] = {
            "sku": row["sku"],
            "name": row["name"],
            "unit_price_cents": int(row["price_cents"]),
        }
    return items


def _load_customers(tax):
    customers = {}
    for row in _read_rows("customers.csv"):
        region = row["region"]
        if region not in tax:
            raise ValueError(f"customer {row['id']} has unknown region {region!r}")
        customers[row["id"]] = {
            "id": row["id"],
            "name": row["name"],
            "region": region,
            "discount_percent": _check_percent(row["discount_pct"], "customers.csv"),
            "tax_percent": tax[region],
        }
    return customers


_TAX = _load_tax()
_ITEMS = _load_items()
_CUSTOMERS = _load_customers(_TAX)


def lookup_item(sku):
    """Return the item for sku as a new dict, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def lookup_customer(customer_id):
    """Return the customer as a new dict, or None if the id is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
