#!/usr/bin/env python3
"""Arithmetic scenarios only: no classification, rate lookup or legal rounding.

Duty methods (field "duty_method"; default inferred):
  ad_valorem   customs_value_jpy x duty_rate_percent / 100
  specific     quantity x duty_specific_jpy_per_unit          (e.g. 27.20 yen/kg)
  compound_sum ad_valorem + specific                           (e.g. "35% + 799 yen/kg")
  greater_of   max(ad_valorem, specific)                      ("x% or y yen/kg, whichever is the greater")
  lesser_of    min(ad_valorem, specific)
Rates must come from tariff_lookup.py output for the import date; put its URL in "rate_source".
"""

import argparse
import json
import re
import sys
from decimal import Decimal, localcontext
from pathlib import Path


ALLOWED = {
    "scenario",
    "rate_source",
    "duty_method",
    "customs_value_jpy",
    "duty_rate_percent",
    "duty_specific_jpy_per_unit",
    "quantity",
    "quantity_unit",
    "consumption_tax_base_jpy",
    "consumption_tax_rate_percent",
}
METHODS = {"ad_valorem", "specific", "compound_sum", "greater_of", "lesser_of"}
NUMBER = re.compile(r"[0-9]{1,18}(?:\.[0-9]{1,8})?\Z")


def amount(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not NUMBER.fullmatch(value):
        raise ValueError(
            f"{key}: require a nonnegative decimal string, at most 18 integer "
            "and 8 fractional digits; no commas, exponents or special values"
        )
    return Decimal(value)


def calculate(data):
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    unknown = set(data) - ALLOWED
    if unknown:
        raise ValueError("unsupported input fields: " + ", ".join(sorted(unknown)))
    scenario = data.get("scenario")
    if not isinstance(scenario, str) or not scenario.strip() or len(scenario) > 200:
        raise ValueError("scenario: require a nonempty string of at most 200 characters")
    tax_fields = {"consumption_tax_base_jpy", "consumption_tax_rate_percent"}
    supplied = tax_fields.intersection(data)
    if supplied and supplied != tax_fields:
        raise ValueError("consumption tax requires BOTH its base and its rate")

    method = data.get("duty_method")
    if method is None:
        method = "specific" if "duty_specific_jpy_per_unit" in data and "duty_rate_percent" not in data else "ad_valorem"
    if method not in METHODS:
        raise ValueError("duty_method must be one of: " + ", ".join(sorted(METHODS)))
    needs_av = method != "specific"
    needs_sp = method != "ad_valorem"
    if needs_sp:
        for key in ("duty_specific_jpy_per_unit", "quantity"):
            if key not in data:
                raise ValueError(f"{method} duty requires '{key}'")
        unit = data.get("quantity_unit")
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("specific duty requires 'quantity_unit' (e.g. 'kg', 'l') matching the tariff line unit")
    if "rate_source" in data and (not isinstance(data["rate_source"], str) or len(data["rate_source"]) > 500):
        raise ValueError("rate_source: require a string of at most 500 characters")

    with localcontext() as ctx:
        ctx.prec = 80
        customs_value = amount(data, "customs_value_jpy")
        values = {"duty_method": method}
        av = sp = None
        if needs_av:
            duty_rate = amount(data, "duty_rate_percent")
            av = customs_value * duty_rate / Decimal(100)
            values["duty_ad_valorem_jpy_unrounded"] = format(av, "f")
        if needs_sp:
            sp = amount(data, "quantity") * amount(data, "duty_specific_jpy_per_unit")
            values["duty_specific_jpy_unrounded"] = format(sp, "f")
        if method == "ad_valorem":
            duty = av
        elif method == "specific":
            duty = sp
        elif method == "compound_sum":
            duty = av + sp
        elif method == "greater_of":
            duty = max(av, sp)
        else:
            duty = min(av, sp)
        values["duty_jpy_unrounded"] = format(duty, "f")
        total = duty
        if supplied:
            tax_base = amount(data, "consumption_tax_base_jpy")
            tax_rate = amount(data, "consumption_tax_rate_percent")
            tax = tax_base * tax_rate / Decimal(100)
            values["consumption_tax_jpy_unrounded"] = format(tax, "f")
            total += tax
        values["sum_of_entered_taxes_jpy_unrounded"] = format(total, "f")
    return {
        "status": "arithmetic_estimate_unrounded",
        "scenario": scenario,
        "inputs": data,
        **values,
        "limitations": [
            "Inputs, classification, rates and tax bases are NOT verified.",
            "Duty method and unit are as entered; quotas, minimum/maximum caps and sugar adjustment levies are not modelled.",
            "No statutory rounding or national/local consumption-tax breakdown.",
            "Only entered taxes are included; no exemptions, other taxes or fees.",
            "Not a final customs payment amount or a landed-cost calculation.",
        ],
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Calculate an UNROUNDED arithmetic scenario from caller-supplied "
            "bases and percentage rates. No HS/rate lookup, source verification "
            "or legal determination. Requires Python 3 standard library only."
        ),
        epilog=(
            'JSON fields: scenario (text), customs_value_jpy (decimal string), and either '
            'duty_rate_percent (ad valorem) or duty_specific_jpy_per_unit + quantity + quantity_unit '
            '(specific duty), or both with duty_method compound_sum|greater_of|lesser_of. '
            'Optional rate_source (tariff_lookup URL). Optional PAIR: consumption_tax_base_jpy and '
            'consumption_tax_rate_percent. Percent 5 means 5%.'
        ),
    )
    parser.add_argument("--input", required=True, type=Path, help="path to scenario JSON")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        result = calculate(data)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
