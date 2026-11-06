"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file.

Committed interface (see shared decision log):
  MONEY_UNIT v4
      All money amounts are integer cents (int). Catalog items carry
      ``price_cents`` (int). ``price`` (float dollars) exists for display
      only and must never be used in tax or total computation.
  PERCENT_REPR v2
      Percentages are fractions in every cross-module field (0.10 = 10%).
  MISSING_LOOKUP_VALUE v2
      get_item / get_customer return None when not found.
      require_item / require_customer raise KeyError when not found.
  TAX_API v3 / TAX_UNKNOWN_REGION v1 (pricing supplies the inputs)
      item_category(sku) -> str or None
      customer_region(cid) -> str or None   (None = no region / unknown customer)

Item record:     {'sku': str, 'name': str, 'category': str,
                  'price_cents': int, 'price': float}
Customer record: {'id': str, 'name': str, 'region': str or None,
                  'discount': Decimal}   # fraction, e.g. Decimal('0.10') for 10%
"""

import csv
import os
from decimal import Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            price_cents = int(row["price_cents"])
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "category": row["category"].strip(),
                "price_cents": price_cents,
                # Display only (MONEY_UNIT v4). Never use this in arithmetic.
                "price": price_cents / 100,
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            region = row["region"].strip() or None
            # discount_pct is stored as a whole percent (e.g. 10); convert to an
            # exact Decimal fraction (0.10) per PERCENT_REPR v2 / TAX_API v3.
            discount = Decimal(row["discount_pct"].strip()).scaleb(-2)
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "region": region,
                "discount": discount,
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the item record for sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def require_item(sku):
    """Return the item record for sku; raise KeyError if sku is unknown."""
    item = get_item(sku)
    if item is None:
        raise KeyError(f"unknown SKU: {sku!r}")
    return item


def get_customer(cid):
    """Return the customer record for cid, or None if cid is unknown."""
    customer = _CUSTOMERS.get(cid)
    return dict(customer) if customer is not None else None


def require_customer(cid):
    """Return the customer record for cid; raise KeyError if cid is unknown."""
    customer = get_customer(cid)
    if customer is None:
        raise KeyError(f"unknown customer id: {cid!r}")
    return customer


def item_category(sku):
    """Return the category of sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return item["category"] if item is not None else None


def customer_region(cid):
    """Return the region code of customer cid, or None if the customer is
    unknown or has no region."""
    customer = _CUSTOMERS.get(cid)
    return customer["region"] if customer is not None else None
