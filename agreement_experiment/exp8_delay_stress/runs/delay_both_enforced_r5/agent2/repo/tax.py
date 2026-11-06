"""Tax module. Owned by agent2. Computes sales tax.

Implements the committed decision TAX_API v1 (see the agreement log).

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (TAX_API v1):
- Money amounts are float dollars (12.5 means $12.50).
- Discounts and rates are float fractions (0.10 means 10%; rate 0.0825 means 8.25%).
  Percent numbers from rates.csv are converted to fractions here.
- A lookup that finds nothing raises KeyError (unknown region string).

Tax rules summary:
- Tax percent depends on the customer's region (rates.csv).
- Lines whose category is listed in exempt_categories.csv are not taxed.
- base = taxable_amount * (1 - discount)
- tax = base * rate, rounded to the cent (half up).
- An unknown customer (region=None) pays 0% tax.
"""

import csv
import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from typing import Iterable, Optional, Tuple

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_FILE = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_FILE = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")


@dataclass(frozen=True)
class TaxResult:
    """Result of a tax computation.

    taxable_amount: sum of the non-exempt line amounts, before discount (float dollars).
    tax_rate:       tax rate as a fraction (e.g. 0.0825 for 8.25%).
    tax_amount:     tax in float dollars, rounded half up to the cent.
    """

    taxable_amount: float
    tax_rate: float
    tax_amount: float


@lru_cache(maxsize=None)
def _load_rates() -> dict:
    """Region -> tax rate as an exact Decimal fraction, read from rates.csv (percent numbers)."""
    rates = {}
    with open(_RATES_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip()) / Decimal(100)
    return rates


@lru_cache(maxsize=None)
def _load_exempt_categories() -> frozenset:
    """Set of exempt category names, read from exempt_categories.csv."""
    with open(_EXEMPT_FILE, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


def _rate_decimal(region: Optional[str]) -> Decimal:
    if region is None:
        # Unknown customer pays 0% tax (RULES.md).
        return Decimal(0)
    rates = _load_rates()
    if region not in rates:
        raise KeyError(f"no tax rate for region {region!r}")
    return rates[region]


def tax_rate(region: Optional[str]) -> float:
    """Tax rate as a fraction for a region. None (unknown customer) gives 0.0.

    Raises KeyError if the region string is not in rates.csv.
    """
    return float(_rate_decimal(region))


def tax_for(
    lines: Iterable[Tuple[float, Optional[str]]],
    region: Optional[str],
    discount: float = 0.0,
) -> TaxResult:
    """Compute sales tax for an order.

    lines:    iterable of (amount, category). amount is float dollars.
              category None means no category, which is taxable.
              Categories listed in exempt_categories.csv are not taxed.
    region:   customer region such as 'TX' (Customer.region). None means
              unknown customer, which gives 0% tax.
    discount: customer discount as a fraction (0.10 means 10%). Default 0.0.
              Must be in [0, 1], otherwise ValueError.

    Raises KeyError for a region string not in rates.csv.
    """
    disc = Decimal(str(discount))
    if disc < 0 or disc > 1:
        raise ValueError(f"discount must be a fraction in [0, 1], got {discount!r}")

    exempt = _load_exempt_categories()
    taxable = Decimal(0)
    for amount, category in lines:
        if category is not None and category in exempt:
            continue
        taxable += Decimal(str(amount))

    rate = _rate_decimal(region)

    # tax = taxable * (1 - discount) * rate, rounded half up to the cent
    raw_tax = taxable * (Decimal(1) - disc) * rate
    tax_amount = raw_tax.quantize(_CENT, rounding=ROUND_HALF_UP)

    return TaxResult(
        taxable_amount=float(taxable),
        tax_rate=float(rate),
        tax_amount=float(tax_amount),
    )
