# Sales tax rules
- The tax percent depends on the customer's region (rates.csv).
- Items whose category is listed in exempt_categories.csv are not taxed.
- Tax base = (sum of the taxable line amounts) reduced by the customer's discount percent:
  base = taxable_amount * (100 - discount_pct) / 100
- tax = base * tax_pct / 100, rounded to the cent (half up).
- An unknown customer pays 0% tax.
