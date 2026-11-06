"""Item and customer information for the invoicing package (agent1 / pricing).

Units (committed decision pricing_api v2):
  * money: integer cents (unit_price_cents)
  * discounts: percent numbers (discount_pct: 10 means 10%)
  * lookups that find nothing return None

This module only returns stored data. It does not apply discounts or
compute totals; invoice.py does the arithmetic and tax.py does tax rules.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _parse_number(text):
    """Parse a CSV number: int if it looks like one, otherwise float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items(path):
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


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return {"sku", "name", "unit_price_cents", "category"} for sku, or None.

    The unit price is raw (no discount, no quantity). Returns a copy so
    callers cannot change the stored data.
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return {"id", "name", "discount_pct", "region"} for customer_id, or None.

    discount_pct is a percent number (10 means 10%). region is the code
    used by tax_api (e.g. "TX"). Returns a copy.
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
