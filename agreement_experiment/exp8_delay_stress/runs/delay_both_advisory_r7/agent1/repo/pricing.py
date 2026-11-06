"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules, following the
committed decision PRICING_API v2:

* money: int cents (1250 means $12.50)
* percent: percent number (10 means 10%), matching the data's discount_pct
* lookups that find nothing return None (never raise)

Data files are in data_pricing/ next to this file:
  catalog.csv   sku,name,price_cents,category
  customers.csv id,name,discount_pct,region
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path=_CATALOG_PATH):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in catalog: {sku!r}")
            price_cents = int(row["price_cents"])
            if price_cents < 0:
                raise ValueError(f"negative price for sku {sku!r}: {price_cents}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": price_cents,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id: {cid!r}")
            discount_pct = int(row["discount_pct"])
            if not 0 <= discount_pct <= 100:
                raise ValueError(f"discount_pct out of range for {cid!r}: {discount_pct}")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": discount_pct,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return {"sku", "name", "unit_price_cents", "category"} for sku, or None."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return {"id", "name", "discount_pct", "region"} for customer_id, or None."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def unit_price_after_discount_cents(customer_id, sku):
    """Unit price in int cents after the customer's discount.

    Computes unit_price_cents * (100 - discount_pct) / 100, rounded half-up
    to a whole cent. Returns None if the customer or sku is unknown.
    """
    item = _ITEMS.get(sku)
    customer = _CUSTOMERS.get(customer_id)
    if item is None or customer is None:
        return None
    numerator = item["unit_price_cents"] * (100 - customer["discount_pct"])
    # Integer half-up rounding of numerator / 100 (numerator is never negative here).
    quotient, remainder = divmod(numerator, 100)
    if 2 * remainder >= 100:
        quotient += 1
    return quotient
