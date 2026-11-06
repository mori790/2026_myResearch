"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules, following the
committed decision ``pricing_api`` v1 in the shared decision log:

* All amounts are integer cents (``int``); no floats anywhere.
* ``discount_pct`` is an integer percent in 0..100 (10 means 10 percent).
* ``get_item(sku)``       -> dict with sku, name, price_cents, category.
* ``get_customer(id)``    -> dict with id, name, discount_pct, region.
* ``apply_discount(amount_cents, customer_id)`` -> discounted amount in cents,
  rounded half up with integer arithmetic.
* Unknown SKUs / customers raise ``UnknownItemError`` / ``UnknownCustomerError``,
  which are subclasses of ``KeyError``.

The data files live in ``data_pricing/`` next to this file and are loaded
relative to this module's location.
"""

import csv
import os

__all__ = [
    "UnknownItemError",
    "UnknownCustomerError",
    "get_item",
    "get_customer",
    "apply_discount",
]

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


class UnknownItemError(KeyError):
    """Raised when a SKU is not in the catalog."""


class UnknownCustomerError(KeyError):
    """Raised when a customer id is not in the customer list."""


def _parse_int(value, field, path, line_no):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{path}:{line_no}: field '{field}' must be an integer, got {value!r}"
        ) from None


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):  # line 1 is the header
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"{path}:{line_no}: duplicate sku {sku!r}")
            price_cents = _parse_int(row["price_cents"], "price_cents", path, line_no)
            if price_cents < 0:
                raise ValueError(f"{path}:{line_no}: price_cents must be >= 0")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": price_cents,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"{path}:{line_no}: duplicate customer id {cid!r}")
            discount_pct = _parse_int(row["discount_pct"], "discount_pct", path, line_no)
            if not 0 <= discount_pct <= 100:
                raise ValueError(f"{path}:{line_no}: discount_pct must be in 0..100")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": discount_pct,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the catalog record for ``sku``.

    Raises UnknownItemError if the sku is not in the catalog.
    """
    try:
        record = _ITEMS[sku]
    except KeyError:
        raise UnknownItemError(sku) from None
    return dict(record)


def get_customer(customer_id):
    """Return a copy of the customer record for ``customer_id``.

    Raises UnknownCustomerError if the customer is not known.
    """
    try:
        record = _CUSTOMERS[customer_id]
    except KeyError:
        raise UnknownCustomerError(customer_id) from None
    return dict(record)


def apply_discount(amount_cents, customer_id):
    """Return the discounted amount in cents for ``customer_id``.

    Rounding rule (committed): (amount_cents * (100 - discount_pct) + 50) // 100,
    i.e. round half up, using integer arithmetic only.
    Raises UnknownCustomerError if the customer is not known.
    """
    if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
        raise TypeError("amount_cents must be an int (cents)")
    discount_pct = get_customer(customer_id)["discount_pct"]
    return (amount_cents * (100 - discount_pct) + 50) // 100
