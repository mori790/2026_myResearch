"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API (committed decision `pricing_api` v1):
    get_item_price(sku: str) -> int | None
        Unit price in integer cents, or None if the sku is unknown.
    get_customer(customer_id: str) -> dict | None
        None if the customer is unknown; otherwise
        {"name": str, "discount_percent": str, "tax_percent": str}
        where the percents are plain decimal strings exactly as in the CSV data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {key.strip(): (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(f)
        ]


def _load_catalog():
    items = {}
    for row in _read_rows("catalog.csv"):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in catalog.csv: {sku!r}")
        items[sku] = {"name": row["name"], "price_cents": int(row["price_cents"])}
    return items


def _load_tax():
    tax = {}
    for row in _read_rows("tax.csv"):
        region = row["region"]
        if region in tax:
            raise ValueError(f"duplicate region in tax.csv: {region!r}")
        tax[region] = row["tax_pct"]
    return tax


def _load_customers():
    customers = {}
    for row in _read_rows("customers.csv"):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
        customers[cid] = {
            "name": row["name"],
            "discount_percent": row["discount_pct"],
            "region": row["region"],
        }
    return customers


_ITEMS = _load_catalog()
_TAX = _load_tax()
_CUSTOMERS = _load_customers()


def get_item_price(sku):
    """Return the unit price of `sku` in integer cents, or None if unknown."""
    item = _ITEMS.get(sku)
    if item is None:
        return None
    return item["price_cents"]


def get_customer(customer_id):
    """Return customer info as a dict, or None if the customer is unknown.

    Raises ValueError if the customer's region has no row in tax.csv, because
    that is a data error that must not be silently priced as 0% tax.
    """
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return None
    region = customer["region"]
    if region not in _TAX:
        raise ValueError(
            f"customer {customer_id!r} has region {region!r} with no row in tax.csv"
        )
    return {
        "name": customer["name"],
        "discount_percent": customer["discount_percent"],
        "tax_percent": _TAX[region],
    }
