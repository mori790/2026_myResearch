"""Pricing data access for the invoicing package.

Loads catalog, customer, and tax data from the ``data/`` directory next to
this module. Implements the committed ``pricing-api`` v1 contract:

- get_item(sku) -> {"sku": str, "name": str, "price_cents": int}
- get_customer(customer_id) -> {"id": str, "name": str,
                                "discount_pct": Decimal, "region": str}
- get_tax_pct(region) -> Decimal (percent, e.g. Decimal("8.25") means 8.25%)

Money is always integer cents. Percentages are Decimal values in percent
units. Unknown SKUs, customer IDs, and regions raise KeyError. This module
does no discount or tax arithmetic; the caller does that.
"""

import csv
import os
from decimal import Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_catalog():
    catalog = {}
    for row in _load_rows("catalog.csv"):
        sku = row["sku"].strip()
        catalog[sku] = {
            "sku": sku,
            "name": row["name"].strip(),
            "price_cents": int(row["price_cents"].strip()),
        }
    return catalog


def _load_customers():
    customers = {}
    for row in _load_rows("customers.csv"):
        customer_id = row["id"].strip()
        customers[customer_id] = {
            "id": customer_id,
            "name": row["name"].strip(),
            "discount_pct": Decimal(row["discount_pct"].strip()),
            "region": row["region"].strip(),
        }
    return customers


def _load_tax():
    tax = {}
    for row in _load_rows("tax.csv"):
        tax[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return tax


_CATALOG = _load_catalog()
_CUSTOMERS = _load_customers()
_TAX = _load_tax()


def get_item(sku):
    """Return item info for ``sku``. Raises KeyError if unknown."""
    item = _CATALOG[sku]
    return dict(item)


def get_customer(customer_id):
    """Return customer info for ``customer_id``. Raises KeyError if unknown."""
    customer = _CUSTOMERS[customer_id]
    return dict(customer)


def get_tax_pct(region):
    """Return the tax rate for ``region`` as a percent. Raises KeyError if unknown."""
    return _TAX[region]
