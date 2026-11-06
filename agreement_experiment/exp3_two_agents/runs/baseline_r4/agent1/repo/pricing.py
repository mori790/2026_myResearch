"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

Public API (agreed with agent2):
  get_unit_price_cents(sku) -> int | None
      Unit price in integer cents, or None if the SKU is unknown.
  get_customer(customer_id) -> dict | None
      {"name": str, "discount_percent": Decimal, "tax_percent": Decimal},
      or None if the customer is unknown.
      tax_percent is looked up from the customer's region in tax.csv.
"""

import csv
import os
from decimal import Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {key.strip(): (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(f)
        ]


def _load_catalog():
    return {row["sku"]: int(row["price_cents"]) for row in _read_rows("catalog.csv")}


def _load_customers():
    return {
        row["id"]: {
            "name": row["name"],
            "discount_percent": Decimal(row["discount_pct"]),
            "region": row["region"],
        }
        for row in _read_rows("customers.csv")
    }


def _load_tax_rates():
    return {row["region"]: Decimal(row["tax_pct"]) for row in _read_rows("tax.csv")}


_CATALOG = _load_catalog()
_CUSTOMERS = _load_customers()
_TAX_RATES = _load_tax_rates()


def get_unit_price_cents(sku):
    """Return the unit price of `sku` in integer cents, or None if unknown."""
    return _CATALOG.get(sku)


def get_customer(customer_id):
    """Return pricing info for a customer, or None if the customer is unknown."""
    record = _CUSTOMERS.get(customer_id)
    if record is None:
        return None
    return {
        "name": record["name"],
        "discount_percent": record["discount_percent"],
        "tax_percent": _TAX_RATES[record["region"]],
    }
