"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

Decision pricing_api v2 (see agreement log):
  - all money values are integer cents
  - percents are integer millipercent (1 unit = 0.001%): 8.875% -> 8875
  - unknown SKU / customer -> None
  - invoice.py does all rounding and formatting
"""

import csv
import os
from decimal import Decimal

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _to_millipct(text):
    """Convert a percent string such as '8.875' into integer millipercent (8875)."""
    value = Decimal(text.strip()) * 1000
    if value != value.to_integral_value():
        raise ValueError(f"percent {text!r} has more than 3 decimal places")
    return int(value)


def _read_csv(name):
    with open(os.path.join(DATA_DIR, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load():
    items = {
        row["sku"].strip(): {"name": row["name"].strip(), "unit_price_cents": int(row["price_cents"])}
        for row in _read_csv("catalog.csv")
    }
    tax = {row["region"].strip(): _to_millipct(row["tax_pct"]) for row in _read_csv("tax.csv")}
    customers = {}
    for row in _read_csv("customers.csv"):
        region = row["region"].strip()
        if region not in tax:
            raise ValueError(f"customer {row['id']} has region {region!r} with no tax entry")
        customers[row["id"].strip()] = {
            "name": row["name"].strip(),
            "region": region,
            "discount_millipct": _to_millipct(row["discount_pct"]),
            "tax_millipct": tax[region],
        }
    return items, customers


_ITEMS, _CUSTOMERS = _load()


def unit_price_cents(sku):
    """Unit price in integer cents for a SKU, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return item["unit_price_cents"] if item else None


def get_customer(customer_id):
    """Customer info dict {name, region, discount_millipct, tax_millipct}, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer else None
