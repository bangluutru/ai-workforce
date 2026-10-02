#!/usr/bin/env python3
"""Arithmetic scenarios only: no classification, rate lookup or legal rounding."""

import argparse
import json
import re
import sys
from decimal import Decimal, localcontext
from pathlib import Path


ALLOWED = {
    "scenario",
    "customs_value_jpy",
    "duty_rate_percent",
    "consumption_tax_base_jpy",
    "consumption_tax_rate_percent",
}
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

    with localcontext() as ctx:
        ctx.prec = 80
        customs_value = amount(data, "customs_value_jpy")
        duty_rate = amount(data, "duty_rate_percent")
        duty = customs_value * duty_rate / Decimal(100)
        values = {"duty_jpy_unrounded": format(duty, "f")}
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
            "Ad valorem duty only; no specific or compound duty.",
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
            'JSON fields: scenario (text), customs_value_jpy and duty_rate_percent '
            '(decimal strings). Optional PAIR: consumption_tax_base_jpy and '
            'consumption_tax_rate_percent (decimal strings). Percent 5 means 5%.'
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
