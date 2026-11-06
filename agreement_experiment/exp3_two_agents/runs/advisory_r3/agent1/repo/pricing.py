"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API: committed decision `pricing_api` v3 in the shared agreement log.
- Money is integer cents everywhere.
- Percentages are float percent units (8.25 means 8.25%).
- Every lookup raises KeyError for an unknown sku, customer id, or region.
- discount_cents and tax_cents round half up to the nearest cent.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_rows(filename):
    with open(os.path.join(DATA_DIR, filename), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_items():
    return {
        row["sku"]: {
            "sku": row["sku"],
            "name": row["name"],
            "unit_price_cents": int(row["price_cents"]),
        }
        for row in _load_rows("catalog.csv")
    }


def _load_customers():
    return {
        row["id"]: {
            "id": row["id"],
            "name": row["name"],
            "discount_pct": float(row["discount_pct"]),
            "region": row["region"],
        }
        for row in _load_rows("customers.csv")
    }


def _load_tax():
    return {row["region"]: float(row["tax_pct"]) for row in _load_rows("tax.csv")}


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()
_TAX_PCT = _load_tax()


def _percent_of_cents(amount_cents, pct):
    # Decimal(str(...)) avoids binary float error, e.g. 8.25% of 2250 must be 185.625.
    exact = Decimal(amount_cents) * Decimal(str(pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def get_item(sku):
    """Return {sku, name, unit_price_cents} for sku. KeyError if unknown."""
    return dict(_ITEMS[sku])


def get_customer(customer_id):
    """Return {id, name, discount_pct, region} for customer_id. KeyError if unknown."""
    return dict(_CUSTOMERS[customer_id])


def get_tax_pct(region):
    """Return the tax rate in percent for region (OR is 0.0). KeyError if unknown."""
    return _TAX_PCT[region]


def discount_cents(subtotal_cents, customer_id):
    """Return the discount in cents for subtotal_cents. KeyError if unknown customer."""
    return _percent_of_cents(subtotal_cents, _CUSTOMERS[customer_id]["discount_pct"])


def tax_cents(taxable_cents, region):
    """Return the tax in cents on taxable_cents for region. KeyError if unknown region."""
    return _percent_of_cents(taxable_cents, _TAX_PCT[region])
