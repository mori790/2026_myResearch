"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API (committed as decision `pricing_api`):
    unit_price_cents(sku) -> int | None
        Unit price of a catalog item in integer cents, or None if unknown.
    get_customer(customer_id) -> dict | None
        {"name": str, "discount_percent": Decimal, "tax_percent": Decimal}
        or None if the customer is unknown. Percents are in percent units
        (Decimal("10") means 10%). tax_percent comes from the customer's region.
"""

import csv
import os
from decimal import Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_rows(filename):
    with open(os.path.join(_DATA_DIR, filename), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_catalog():
    return {
        row["sku"].strip(): int(row["price_cents"])
        for row in _read_rows("catalog.csv")
    }


def _load_tax_rates():
    return {
        row["region"].strip(): Decimal(row["tax_pct"].strip())
        for row in _read_rows("tax.csv")
    }


def _load_customers():
    return {
        row["id"].strip(): {
            "name": row["name"].strip(),
            "discount_percent": Decimal(row["discount_pct"].strip()),
            "region": row["region"].strip(),
        }
        for row in _read_rows("customers.csv")
    }


_CATALOG = _load_catalog()
_TAX_RATES = _load_tax_rates()
_CUSTOMERS = _load_customers()


def unit_price_cents(sku):
    """Return the unit price of `sku` in integer cents, or None if unknown."""
    return _CATALOG.get(sku)


def get_customer(customer_id):
    """Return name, discount_percent and tax_percent for a customer, or None.

    tax_percent is looked up from the customer's region in tax.csv.
    """
    record = _CUSTOMERS.get(customer_id)
    if record is None:
        return None
    return {
        "name": record["name"],
        "discount_percent": record["discount_percent"],
        "tax_percent": _TAX_RATES.get(record["region"], Decimal("0")),
    }
