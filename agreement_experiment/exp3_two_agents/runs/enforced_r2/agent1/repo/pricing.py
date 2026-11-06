"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

Public API (agreed with agent2, see agreement topic "pricing_api" v1):

    unit_price_cents(sku: str) -> int | None
        Price of one unit in integer cents, or None if the SKU is unknown.

    get_customer(customer_id: str) -> dict | None
        None if the customer is unknown. Otherwise a dict with keys
        "name", "discount_percent", "tax_percent". The percents are decimal
        strings exactly as stored in the data files (e.g. "10", "8.25", "0").
        The tax rate is looked up from tax.csv using the customer's region.

Money is never a float here; prices are integer cents. Rounding is not done
in this module (that is invoice.py's job).
"""

import csv
import os
from decimal import Decimal, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k.strip(): (v or "").strip() for k, v in row.items() if k is not None})
    return rows


def _check_percent(value, where):
    """Make sure a percent string is a valid decimal; return it unchanged."""
    try:
        Decimal(value)
    except InvalidOperation:
        raise ValueError(f"{where}: not a decimal percent: {value!r}")
    return value


def _load_catalog():
    catalog = {}
    for row in _read_rows("catalog.csv"):
        sku = row["sku"]
        if sku in catalog:
            raise ValueError(f"catalog.csv: duplicate sku {sku!r}")
        price = row["price_cents"]
        if not price.isdigit():
            raise ValueError(f"catalog.csv: price_cents must be a non-negative integer for sku {sku!r}: {price!r}")
        catalog[sku] = int(price)
    return catalog


def _load_tax():
    tax = {}
    for row in _read_rows("tax.csv"):
        region = row["region"]
        if region in tax:
            raise ValueError(f"tax.csv: duplicate region {region!r}")
        tax[region] = _check_percent(row["tax_pct"], f"tax.csv region {region!r}")
    return tax


def _load_customers(tax):
    customers = {}
    for row in _read_rows("customers.csv"):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"customers.csv: duplicate customer id {cid!r}")
        region = row["region"]
        if region not in tax:
            # Fail loudly at load time: a customer whose region has no tax rate
            # would otherwise get an invoice with silently wrong tax.
            raise ValueError(f"customers.csv: customer {cid!r} has region {region!r} with no row in tax.csv")
        customers[cid] = {
            "name": row["name"],
            "discount_percent": _check_percent(row["discount_pct"], f"customers.csv customer {cid!r}"),
            "tax_percent": tax[region],
        }
    return customers


_CATALOG = _load_catalog()
_TAX = _load_tax()
_CUSTOMERS = _load_customers(_TAX)


def unit_price_cents(sku):
    """Return the unit price of `sku` in integer cents, or None if unknown."""
    return _CATALOG.get(sku.strip())


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id.strip())
    if customer is None:
        return None
    return dict(customer)
