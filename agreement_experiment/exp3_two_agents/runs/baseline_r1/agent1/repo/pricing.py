"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API (agreed in the shared agreement log as topic "pricing_api", v1):
  get_unit_price_cents(sku)       -> int cents, or None if the SKU is unknown
  get_customer(customer_id)       -> {"name": str,
                                      "discount_percent": str,
                                      "tax_percent": str}
                                     or None if the customer is unknown.
                                     Percents are decimal strings, e.g. "10", "8.25".

Money is never returned as float. Rounding is done by the caller (invoice.py).
"""

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _read_rows(filename):
    """Read a CSV file from DATA_DIR and return its rows as stripped dicts."""
    with open(DATA_DIR / filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {key.strip(): (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def _checked_percent(text, where):
    """Return text as a decimal string after checking it is a valid number."""
    try:
        Decimal(text)
    except InvalidOperation:
        raise ValueError(f"invalid percent {text!r} in {where}") from None
    return text


def _load_catalog():
    catalog = {}
    for row in _read_rows("catalog.csv"):
        sku = row["sku"]
        if sku in catalog:
            raise ValueError(f"duplicate SKU {sku!r} in catalog.csv")
        catalog[sku] = int(row["price_cents"])
    return catalog


def _load_customers():
    customers = {}
    for row in _read_rows("customers.csv"):
        customers[row["id"]] = {
            "name": row["name"],
            "discount_percent": _checked_percent(
                row["discount_pct"], f"customers.csv (customer {row['id']})"
            ),
            "region": row["region"],
        }
    return customers


def _load_tax_rates():
    rates = {}
    for row in _read_rows("tax.csv"):
        rates[row["region"]] = _checked_percent(
            row["tax_pct"], f"tax.csv (region {row['region']})"
        )
    return rates


_CATALOG = _load_catalog()
_CUSTOMERS = _load_customers()
_TAX_RATES = _load_tax_rates()


def get_unit_price_cents(sku):
    """Return the unit price of ``sku`` in integer cents, or None if unknown."""
    return _CATALOG.get(str(sku).strip())


def get_customer(customer_id):
    """Return name, discount and tax percent for a customer, or None if unknown.

    The tax percent comes from the customer's region in tax.csv.
    Raises ValueError if the customer's region has no tax rate.
    """
    customer = _CUSTOMERS.get(str(customer_id).strip())
    if customer is None:
        return None
    region = customer["region"]
    if region not in _TAX_RATES:
        raise ValueError(
            f"no tax rate for region {region!r} (customer {customer_id!r})"
        )
    return {
        "name": customer["name"],
        "discount_percent": customer["discount_percent"],
        "tax_percent": _TAX_RATES[region],
    }
