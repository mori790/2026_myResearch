"""Item and customer information for the invoicing package.

Implements the committed decision `pricing_api` (v2):
  - money is integer cents (1250 = $12.50)
  - percentages are percent numbers (10 = 10%)
  - lookups return None when nothing is found

Data files live in data_pricing/ next to this module:
  catalog.csv   : sku,name,price_cents,category
  customers.csv : id,name,discount_pct,region
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _parse_number(text):
    """Parse a CSV numeric field: integer when possible, otherwise float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_catalog(path):
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


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return {sku, name, unit_price_cents, category} for sku, or None if unknown.

    A copy is returned so callers cannot modify the loaded catalog.
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return {id, name, discount_pct, region} for customer_id, or None if unknown.

    discount_pct is a percent number (10 = 10%); 0 if the customer has no discount.
    A copy is returned so callers cannot modify the loaded customer data.
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
